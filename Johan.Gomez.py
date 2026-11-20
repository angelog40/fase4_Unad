"""
Sistema Integral de Gestión de Clientes, Servicios y Reservas - Software FJ
Sin bases de datos: todo se maneja con objetos y listas internas.
Los archivos se usan únicamente para el registro de eventos y errores (logs).
"""
import logging
import re
from abc import ABC, abstractmethod

# ---------------------------------------------------------------------------
# Configuración de logs (eventos relevantes + errores)
# ---------------------------------------------------------------------------
logging.basicConfig(
    filename="sistema_eventos.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)

IMPUESTO_DEFECTO = 0.19


# ---------------------------------------------------------------------------
# Excepciones personalizadas
# ---------------------------------------------------------------------------
class SistemaGestionError(Exception):
    """Excepción base del sistema."""


class ClienteInvalidoError(SistemaGestionError):
    """Datos de cliente inválidos."""


class ServicioInvalidoError(SistemaGestionError):
    """Datos de servicio inválidos al crearlo."""


class ServicioNoDisponibleError(SistemaGestionError):
    """El servicio ya está reservado u ocupado."""


class ReservaInvalidaError(SistemaGestionError):
    """Parámetros o cálculos de reserva inconsistentes."""


class OperacionNoPermitidaError(SistemaGestionError):
    """Operación no válida para el estado actual."""


# ---------------------------------------------------------------------------
# Clase abstracta general
# ---------------------------------------------------------------------------
class EntidadGeneral(ABC):
    """Representa cualquier entidad del sistema (clientes, servicios...)."""

    @abstractmethod
    def obtener_identificador(self):
        ...

    @abstractmethod
    def describir_entidad(self):
        ...


# ---------------------------------------------------------------------------
# Cliente (encapsulación + validaciones)
# ---------------------------------------------------------------------------
class Cliente(EntidadGeneral):
    _PATRON_CORREO = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")

    def __init__(self, identificacion, nombre, correo):
        self.__identificacion = identificacion
        self.__nombre = nombre
        self.__correo = correo
        self.validar_datos()

    def validar_datos(self):
        if not isinstance(self.__identificacion, str) or not self.__identificacion.strip():
            raise ClienteInvalidoError("La identificación debe ser un texto no vacío.")
        if not isinstance(self.__nombre, str) or len(self.__nombre.strip()) < 3:
            raise ClienteInvalidoError("El nombre debe tener al menos 3 caracteres.")
        if not isinstance(self.__correo, str) or not self._PATRON_CORREO.match(self.__correo):
            raise ClienteInvalidoError(f"El correo '{self.__correo}' no tiene un formato válido.")

    # Solo lectura: los datos personales no se modifican desde fuera
    @property
    def identificacion(self):
        return self.__identificacion

    @property
    def nombre(self):
        return self.__nombre

    @property
    def correo(self):
        return self.__correo

    def obtener_identificador(self):
        return self.__identificacion

    def describir_entidad(self):
        return f"Cliente: {self.__nombre} ({self.__correo})"


# ---------------------------------------------------------------------------
# Servicio (abstracta) y servicios especializados
# ---------------------------------------------------------------------------
class Servicio(EntidadGeneral):
    def __init__(self, id_servicio, tarifa_base):
        if not isinstance(id_servicio, str) or not id_servicio.strip():
            raise ServicioInvalidoError("El servicio debe tener un identificador válido.")
        if isinstance(tarifa_base, bool) or not isinstance(tarifa_base, (int, float)) or tarifa_base <= 0:
            raise ServicioInvalidoError(f"La tarifa base '{tarifa_base}' debe ser un número positivo.")
        self.id_servicio = id_servicio
        self.tarifa_base = float(tarifa_base)
        self.disponible = True

    def obtener_identificador(self):
        return self.id_servicio

    def validar_parametros(self, duracion, impuesto=0.0, descuento=0.0):
        """Validación común; las subclases pueden sobrescribirla y ampliarla."""
        for nombre, valor in (("duración", duracion), ("impuesto", impuesto), ("descuento", descuento)):
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                raise TypeError(f"El parámetro {nombre} debe ser numérico.")
        if duracion <= 0:
            raise ValueError("La duración debe ser mayor a 0.")
        if not 0 <= impuesto <= 1:
            raise ValueError("El impuesto debe estar entre 0 y 1.")
        if not 0 <= descuento <= 1:
            raise ValueError("El descuento debe estar entre 0 y 1.")

    @staticmethod
    def _aplicar_ajustes(costo, impuesto, descuento):
        costo += costo * impuesto
        costo -= costo * descuento
        return costo

    @abstractmethod
    def calcular_costo(self, duracion, impuesto=0.0, descuento=0.0):
        """Sobrecarga simulada: parámetros opcionales de impuesto y descuento."""

    # Variantes adicionales del cálculo (más "sobrecarga")
    def calcular_costo_con_impuesto(self, duracion, impuesto=IMPUESTO_DEFECTO):
        return self.calcular_costo(duracion, impuesto=impuesto)

    def calcular_costo_con_descuento(self, duracion, descuento):
        return self.calcular_costo(duracion, descuento=descuento)


class ReservaSala(Servicio):
    MAX_HORAS = 12

    def validar_parametros(self, duracion, impuesto=0.0, descuento=0.0):
        super().validar_parametros(duracion, impuesto, descuento)
        if duracion > self.MAX_HORAS:
            raise ValueError(f"Una sala no se puede reservar más de {self.MAX_HORAS} horas.")

    def calcular_costo(self, duracion, impuesto=0.0, descuento=0.0):
        self.validar_parametros(duracion, impuesto, descuento)
        return self._aplicar_ajustes(self.tarifa_base * duracion, impuesto, descuento)

    def describir_entidad(self):
        return f"Reserva de Sala (ID: {self.id_servicio})"


class AlquilerEquipo(Servicio):
    CARGO_MANTENIMIENTO = 15.0

    def calcular_costo(self, duracion, impuesto=0.0, descuento=0.0):
        self.validar_parametros(duracion, impuesto, descuento)
        costo = self.tarifa_base * duracion + self.CARGO_MANTENIMIENTO
        return self._aplicar_ajustes(costo, impuesto, descuento)

    def describir_entidad(self):
        return f"Alquiler de Equipo Informático (ID: {self.id_servicio})"


class AsesoriaEspecializada(Servicio):
    HORAS_MINIMAS = 1

    def validar_parametros(self, duracion, impuesto=0.0, descuento=0.0):
        super().validar_parametros(duracion, impuesto, descuento)
        if duracion < self.HORAS_MINIMAS:
            raise ValueError(f"La asesoría requiere mínimo {self.HORAS_MINIMAS} hora.")

    def calcular_costo(self, duracion, impuesto=0.0, descuento=0.0):
        self.validar_parametros(duracion, impuesto, descuento)
        return self._aplicar_ajustes(self.tarifa_base * duracion, impuesto, descuento)

    def describir_entidad(self):
        return f"Asesoría Especializada (ID: {self.id_servicio})"


# ---------------------------------------------------------------------------
# Reserva
# ---------------------------------------------------------------------------
class Reserva:
    def __init__(self, cliente, servicio, duracion):
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva requiere un cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva requiere un servicio válido.")
        self.cliente = cliente
        self.servicio = servicio
        self.duracion = duracion
        self.estado = "Pendiente"
        self.costo_total = None

    def confirmar(self):
        """Confirma la reserva; lanza excepciones personalizadas si no es posible."""
        if self.estado != "Pendiente":
            raise OperacionNoPermitidaError(f"No se puede confirmar una reserva en estado '{self.estado}'.")
        if not self.servicio.disponible:
            raise ServicioNoDisponibleError(
                f"El servicio {self.servicio.obtener_identificador()} no está disponible."
            )
        try:
            costo = self.servicio.calcular_costo(self.duracion, impuesto=IMPUESTO_DEFECTO)
        except (TypeError, ValueError) as e:
            # Encadenamiento de excepciones
            raise ReservaInvalidaError(f"Parámetros inválidos para calcular el costo: {e}") from e
        if costo <= 0:
            raise ReservaInvalidaError("El cálculo del costo es inconsistente (resultado <= 0).")
        self.costo_total = costo
        self.servicio.disponible = False
        self.estado = "Confirmada"

    def cancelar(self):
        if self.estado != "Confirmada":
            raise OperacionNoPermitidaError(f"Solo se puede cancelar una reserva confirmada (estado: '{self.estado}').")
        self.servicio.disponible = True
        self.estado = "Cancelada"
        logging.info(f"Reserva cancelada: {self.cliente.obtener_identificador()} - {self.servicio.obtener_identificador()}")

    def procesar_reserva(self):
        """Procesa la reserva sin detener el programa. Devuelve True si fue exitosa."""
        try:
            self.confirmar()
        except SistemaGestionError as e:
            self.estado = "Fallida" if self.estado == "Pendiente" else self.estado
            logging.error(f"Error procesando reserva: {e}")
            print(f"  [X] No se pudo procesar la reserva. Razón: {e}")
            return False
        except Exception as e:  # error inesperado: se registra y el sistema sigue activo
            self.estado = "Fallida"
            logging.error(f"Error inesperado procesando reserva: {e!r}")
            print(f"  [X] Error inesperado: {e}")
            return False
        else:
            logging.info(
                f"Reserva confirmada: {self.cliente.describir_entidad()} | "
                f"{self.servicio.describir_entidad()} | Costo: {self.costo_total:.2f}"
            )
            print(
                f"  [OK] Reserva confirmada: {self.cliente.describir_entidad()} | "
                f"{self.servicio.describir_entidad()} | Costo total: ${self.costo_total:,.2f}"
            )
            return True
        finally:
            logging.info(f"Intento de procesamiento finalizado para cliente {self.cliente.obtener_identificador()}.")


# ---------------------------------------------------------------------------
# Sistema: gestiona las listas internas (sin base de datos)
# ---------------------------------------------------------------------------
class SistemaGestion:
    def __init__(self):
        self.clientes = []
        self.servicios = []
        self.reservas = []

    def _buscar(self, lista, identificador):
        for item in lista:
            if item.obtener_identificador() == identificador:
                return item
        return None

    def registrar_cliente(self, *args, **kwargs):
        try:
            cliente = Cliente(*args, **kwargs)
            if self._buscar(self.clientes, cliente.identificacion):
                raise ClienteInvalidoError(f"Ya existe un cliente con identificación {cliente.identificacion}.")
        except TypeError as e:  # parámetros faltantes o sobrantes
            logging.error(f"Parámetros faltantes al registrar cliente: {e}")
            print(f"  [X] Registro de cliente fallido (parámetros): {e}")
            return None
        except ClienteInvalidoError as e:
            logging.error(f"Registro de cliente fallido: {e}")
            print(f"  [X] Registro de cliente fallido: {e}")
            return None
        self.clientes.append(cliente)
        logging.info(f"Cliente registrado: {cliente.describir_entidad()}")
        print(f"  [OK] {cliente.describir_entidad()} registrado.")
        return cliente

    def registrar_servicio(self, clase_servicio, *args, **kwargs):
        try:
            servicio = clase_servicio(*args, **kwargs)
            if self._buscar(self.servicios, servicio.obtener_identificador()):
                raise ServicioInvalidoError(f"Ya existe el servicio {servicio.obtener_identificador()}.")
        except TypeError as e:
            logging.error(f"Parámetros faltantes al crear servicio: {e}")
            print(f"  [X] Creación de servicio fallida (parámetros): {e}")
            return None
        except ServicioInvalidoError as e:
            logging.error(f"Creación de servicio fallida: {e}")
            print(f"  [X] Creación de servicio fallida: {e}")
            return None
        self.servicios.append(servicio)
        logging.info(f"Servicio creado: {servicio.describir_entidad()}")
        print(f"  [OK] {servicio.describir_entidad()} creado.")
        return servicio

    def crear_reserva(self, id_cliente, id_servicio, duracion):
        try:
            cliente = self._buscar(self.clientes, id_cliente)
            servicio = self._buscar(self.servicios, id_servicio)
            reserva = Reserva(cliente, servicio, duracion)  # valida que existan
        except ReservaInvalidaError as e:
            logging.error(f"Creación de reserva fallida ({id_cliente}, {id_servicio}): {e}")
            print(f"  [X] Creación de reserva fallida: {e}")
            return None
        self.reservas.append(reserva)
        reserva.procesar_reserva()
        return reserva


# ---------------------------------------------------------------------------
# Simulación de 12 operaciones
# ---------------------------------------------------------------------------
def simular_operaciones():
    print("--- INICIANDO SIMULACIÓN DE OPERACIONES SOFTWARE FJ ---")
    logging.info("=== Inicio de la simulación ===")
    sistema = SistemaGestion()

    print("\n1. Registro válido de cliente")
    sistema.registrar_cliente("1001", "Ana Gómez", "ana@correo.com")

    print("\n2. Registro inválido de cliente (correo sin @)")
    sistema.registrar_cliente("1002", "Luis Pérez", "luiscorreo.com")

    print("\n3. Registro inválido de cliente (parámetro faltante)")
    sistema.registrar_cliente("1004", "Marta Díaz")

    print("\n4. Registro válido de otro cliente")
    sistema.registrar_cliente("1003", "Carlos Ruiz", "carlos@correo.com")

    print("\n5. Creación correcta de los tres servicios")
    sistema.registrar_servicio(ReservaSala, "S-01", 50.0)
    sistema.registrar_servicio(AlquilerEquipo, "E-01", 30.0)
    sistema.registrar_servicio(AsesoriaEspecializada, "A-01", 100.0)

    print("\n6. Creación incorrecta de servicio (tarifa negativa)")
    sistema.registrar_servicio(AlquilerEquipo, "E-02", -10)

    print("\n7. Reserva exitosa (sala, 4 horas, con impuesto)")
    sistema.crear_reserva("1001", "S-01", 4)

    print("\n8. Reserva fallida: servicio no disponible (la sala ya fue reservada)")
    sistema.crear_reserva("1003", "S-01", 2)

    print("\n9. Reserva fallida: duración inválida (excepción encadenada)")
    sistema.crear_reserva("1001", "E-01", -5)

    print("\n10. Reserva fallida: cliente inexistente")
    sistema.crear_reserva("9999", "A-01", 2)

    print("\n11. Cálculo con parámetros opcionales (impuesto y descuento)")
    try:
        asesoria = sistema.servicios[2]
        costo = asesoria.calcular_costo(duracion=2, impuesto=0.19, descuento=0.10)
        print(f"  [OK] Asesoría con impuesto y descuento: ${costo:,.2f}")
        print(f"  [OK] Solo con descuento del 20%: ${asesoria.calcular_costo_con_descuento(2, 0.20):,.2f}")
        logging.info(f"Consulta de tarifa realizada: {costo:.2f}")
    except Exception as e:
        logging.error(f"Error en consulta de tarifa: {e}")

    print("\n12. Cancelación de reserva y nueva reserva del mismo servicio")
    reserva_sala = sistema.reservas[0]
    try:
        reserva_sala.cancelar()
        print(f"  [OK] Reserva cancelada. Estado: {reserva_sala.estado}")
        reserva_sala.cancelar()  # segunda cancelación: operación no permitida
    except OperacionNoPermitidaError as e:
        logging.error(f"Cancelación no permitida: {e}")
        print(f"  [X] {e}")
    sistema.crear_reserva("1003", "S-01", 2)

    print("\n--- RESUMEN ---")
    print(f"Clientes: {len(sistema.clientes)} | Servicios: {len(sistema.servicios)} | Reservas: {len(sistema.reservas)}")
    for r in sistema.reservas:
        print(f"  - {r.cliente.nombre} -> {r.servicio.describir_entidad()} [{r.estado}]")
    logging.info("=== Fin de la simulación ===")
    print("Simulación finalizada. Revisa 'sistema_eventos.log'.")


if __name__ == "__main__":
    simular_operaciones()