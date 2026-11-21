import logging
from abc import ABC, abstractmethod



# Configuracion de logs (Eventos y errores)

# Se usa level=logging.INFO para registrar tanto eventos relevantes como errores
logging.basicConfig(
    filename='sistema_eventos.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)



# Exepciones personalizadas

class SistemaGestionError(Exception):
    """Excepción base para el sistema de gestión de Software FJ."""
    pass


class ClienteInvalidoError(SistemaGestionError):
    """Se lanza cuando los datos de un cliente son inválidos."""
    pass


class ServicioInvalidoError(SistemaGestionError):
    """Se lanza cuando los parámetros de creación de un servicio son incorrectos."""
    pass


class ServicioNoDisponibleError(SistemaGestionError):
    """Se lanza cuando se intenta reservar un servicio ocupado."""
    pass


class ReservaInvalidaError(SistemaGestionError):
    """Se lanza cuando ocurre un error al procesar o cancelar una reserva."""
    pass



# Clase abstracta general

class EntidadGeneral(ABC):
    """Clase abstracta base para todas las entidades del sistema."""

    @abstractmethod
    def obtener_identificador(self):
        """Retorna el identificador único de la entidad."""
        pass

    @abstractmethod
    def describir_entidad(self):
        """Retorna una descripción legible de la entidad."""
        pass



# Clase cliente con encapsulacion

class Cliente(EntidadGeneral):
    """Representa un cliente con datos personales encapsulados y validados."""

    def __init__(self, identificacion, nombre, correo):
        self.__identificacion = identificacion
        self.__nombre = nombre
        self.__correo = correo
        self.validar_datos()
        logging.info(f"Cliente registrado exitosamente: {self.__identificacion} - {self.__nombre}")

    def validar_datos(self):
        """Valida que la identificación, nombre y correo cumplan el formato mínimo."""
        if not self.__identificacion or not self.__nombre:
            raise ClienteInvalidoError("El cliente debe tener identificación y nombre válidos.")
        if not self.__correo or "@" not in self.__correo:
            raise ClienteInvalidoError(f"El correo '{self.__correo}' no tiene un formato válido.")

    def obtener_identificador(self):
        return self.__identificacion

    def describir_entidad(self):
        return f"Cliente: {self.__nombre} ({self.__correo})"



# Clase abstracta servicio y derivada

class Servicio(EntidadGeneral):
    """Clase abstracta para los servicios ofrecidos por Software FJ."""

    def __init__(self, id_servicio, tarifa_base):
        self.id_servicio = id_servicio
        self.tarifa_base = tarifa_base
        self.disponible = True
        # Ejecuta la validación específica de cada subclase al instanciar
        self.validar_parametros()
        logging.info(f"Servicio creado exitosamente: {self.describir_entidad()} | Tarifa: ${self.tarifa_base:.2f}")

    def obtener_identificador(self):
        return self.id_servicio

    @abstractmethod
    def validar_parametros(self):
        """Valida los parámetros específicos de cada tipo de servicio."""
        pass

    @abstractmethod
    def calcular_costo(self, duracion, impuesto=0.0, descuento=0.0):
        """Calcula el costo total simulando sobrecarga con parámetros opcionales."""
        pass


class ReservaSala(Servicio):
    """Servicio especializado para reserva de salas."""

    def validar_parametros(self):
        if not self.id_servicio or not self.id_servicio.startswith("S-"):
            raise ServicioInvalidoError(f"ID inválido para sala ('{self.id_servicio}'). Debe iniciar con 'S-'.")
        if self.tarifa_base <= 0:
            raise ServicioInvalidoError("La tarifa base de la sala debe ser mayor a 0.")

    def calcular_costo(self, duracion, impuesto=0.0, descuento=0.0):
        costo = self.tarifa_base * duracion
        costo += costo * impuesto
        costo -= costo * descuento
        return costo

    def describir_entidad(self):
        return f"Reserva de Sala (ID: {self.id_servicio})"


class AlquilerEquipo(Servicio):
    """Servicio especializado para alquiler de equipos informáticos."""

    def validar_parametros(self):
        if not self.id_servicio or not self.id_servicio.startswith("E-"):
            raise ServicioInvalidoError(f"ID inválido para equipo ('{self.id_servicio}'). Debe iniciar con 'E-'.")
        if self.tarifa_base <= 0:
            raise ServicioInvalidoError("La tarifa base del equipo debe ser mayor a 0.")

    def calcular_costo(self, duracion, impuesto=0.0, descuento=0.0):
        # Incluye cargo fijo de $15.0 por mantenimiento de equipo
        costo = (self.tarifa_base * duracion) + 15.0
        costo += costo * impuesto
        costo -= costo * descuento
        return costo

    def describir_entidad(self):
        return f"Alquiler de Equipo Informático (ID: {self.id_servicio})"


class AsesoriaEspecializada(Servicio):
    """Servicio especializado para asesorías técnicas."""

    def validar_parametros(self):
        if not self.id_servicio or not self.id_servicio.startswith("A-"):
            raise ServicioInvalidoError(f"ID inválido para asesoría ('{self.id_servicio}'). Debe iniciar con 'A-'.")
        if self.tarifa_base < 20.0:
            raise ServicioInvalidoError("La tarifa mínima para una asesoría especializada es de $20.00.")

    def calcular_costo(self, duracion, impuesto=0.0, descuento=0.0):
        costo = self.tarifa_base * duracion
        costo += costo * impuesto
        costo -= costo * descuento
        return costo

    def describir_entidad(self):
        return f"Asesoría Especializada (ID: {self.id_servicio})"



# Clase reserva

class Reserva:
    """Integra un cliente, un servicio, la duración y el estado de la reserva."""

    def __init__(self, cliente, servicio, duracion):
        self.cliente = cliente
        self.servicio = servicio
        self.duracion = duracion
        self.estado = "Pendiente"

    def procesar_reserva(self):
        """Valida disponibilidad, calcula costo y confirma o rechaza la reserva."""
        try:
            if not self.servicio.disponible:
                raise ServicioNoDisponibleError(
                    f"El servicio {self.servicio.obtener_identificador()} no está disponible."
                )
            if self.duracion <= 0:
                raise ReservaInvalidaError("La duración de la reserva debe ser mayor a 0.")

            # Bloque try/except/else/finally con encadenamiento de excepciones
            try:
                costo_total = self.servicio.calcular_costo(self.duracion, impuesto=0.19)
            except Exception as e:
                raise ReservaInvalidaError("Error al calcular los costos de la reserva.") from e
            else:
                self.estado = "Confirmada"
                self.servicio.disponible = False
                mensaje = (
                    f"Reserva Confirmada: {self.cliente.describir_entidad()} | "
                    f"{self.servicio.describir_entidad()} | Costo Total: ${costo_total:.2f}"
                )
                logging.info(mensaje)
                print(mensaje)
            finally:
                print(f"Intento de procesamiento finalizado para cliente {self.cliente.obtener_identificador()}.")

        except (ServicioNoDisponibleError, ReservaInvalidaError) as e:
            logging.error(f"Error procesando reserva: {e}")
            self.estado = "Fallida"
            print(f"No se pudo procesar la reserva. Razón: {e}")

    def cancelar_reserva(self):
        """Cancela una reserva confirmada y libera el servicio."""
        try:
            if self.estado != "Confirmada":
                raise ReservaInvalidaError(f"No se puede cancelar una reserva en estado '{self.estado}'.")
            self.estado = "Cancelada"
            self.servicio.disponible = True
            mensaje = (
                f"Reserva cancelada exitosamente. El servicio "
                f"{self.servicio.obtener_identificador()} vuelve a estar disponible."
            )
            logging.info(mensaje)
            print(mensaje)
        except ReservaInvalidaError as e:
            logging.error(f"Error al cancelar reserva: {e}")
            print(f"Error: {e}")



# Simulacion de operaciones

def simular_operaciones():
    """Ejecuta operaciones válidas e inválidas demostrando tolerancia a fallos."""
    print("\n--- INICIANDO SIMULACIÓN DE OPERACIONES SOFTWARE FJ ---")
    logging.info("Inicio de simulación automática de operaciones.")

    # 1. Registro válido de cliente
    c1 = Cliente("1001", "Ana Gomez", "ana@correo.com")

    # 2. Registro inválido de cliente (falla formato de correo)
    try:
        c2 = Cliente("1002", "Luis Perez", "luiscorreo.com")
    except ClienteInvalidoError as e:
        logging.error(f"Operación 2 fallida: {e}")
        print(f"[Simulación Op 2 - Error controlado] {e}")

    c3 = Cliente("1003", "Carlos Ruiz", "carlos@correo.com")

    # 3. Creación correcta de servicios
    s_sala = ReservaSala("S-01", 50.0)
    s_equipo = AlquilerEquipo("E-01", 30.0)
    s_asesoria = AsesoriaEspecializada("A-01", 100.0)

    # 4. Creación incorrecta de servicio (tarifa negativa)
    try:
        s_invalido_1 = ReservaSala("S-02", -40.0)
    except ServicioInvalidoError as e:
        logging.error(f"Operación 4 fallida: {e}")
        print(f"[Simulación Op 4 - Error controlado] {e}")

    # 5. Creación incorrecta de servicio (prefijo de ID incorrecto)
    try:
        s_invalido_2 = AsesoriaEspecializada("X-99", 80.0)
    except ServicioInvalidoError as e:
        logging.error(f"Operación 5 fallida: {e}")
        print(f"[Simulación Op 5 - Error controlado] {e}")

    # 6. Reserva exitosa (costo con impuesto del 19%)
    r1 = Reserva(c1, s_sala, 4)
    r1.procesar_reserva()

    # 7. Reserva fallida: Servicio no disponible (ocupado en operación 6)
    r2 = Reserva(c3, s_sala, 2)
    r2.procesar_reserva()

    # 8. Reserva fallida: Duración inválida
    r3 = Reserva(c1, s_equipo, -5)
    r3.procesar_reserva()

    # 9. Cancelación exitosa de reserva y nueva consulta con descuento (sobrecarga)
    r1.cancelar_reserva()
    try:
        costo_descuento = s_asesoria.calcular_costo(duracion=2, impuesto=0.19, descuento=0.10)
        logging.info(f"Consulta de tarifa con descuento realizada: ${costo_descuento:.2f}")
        print(f"Consulta de tarifa con descuento: ${costo_descuento:.2f}")
    except Exception as e:
        logging.error(f"Error en consulta: {e}")

    # 10. Forzar error de validación tras manipulación indebida
    try:
        c1._Cliente__identificacion = None
        c1.validar_datos()
    except ClienteInvalidoError as e:
        logging.error(f"Operación 10 fallida: {e}")
        print(f"[Simulación Op 10 - Error controlado] {e}")

    logging.info("Fin de simulación automática de operaciones.")
    print("--- FIN DE LA SIMULACIÓN ---")



# Menu intercativo por consola

def menu_interactivo():
    """Menú principal para operar el sistema manualmente o lanzar la simulación."""
    clientes = []
    servicios = [
        ReservaSala("S-01", 50.0),
        AlquilerEquipo("E-01", 30.0),
        AsesoriaEspecializada("A-01", 100.0)
    ]
    reservas = []

    while True:
        print("\n=== SISTEMA DE GESTIÓN - SOFTWARE FJ ===")
        print("1. Registrar cliente")
        print("2. Ver servicios disponibles")
        print("3. Crear reserva")
        print("4. Cancelar reserva")
        print("5. Ver reservas registradas")
        print("6. Ejecutar simulación automática (10 operaciones)")
        print("0. Salir")

        opcion = input("Seleccione una opción: ").strip()

        try:
            if opcion == "1":
                id_cli = input("Identificación: ").strip()
                nombre = input("Nombre completo: ").strip()
                correo = input("Correo electrónico: ").strip()
                nuevo_cliente = Cliente(id_cli, nombre, correo)
                clientes.append(nuevo_cliente)
                print(f"Cliente registrado: {nuevo_cliente.describir_entidad()}")

            elif opcion == "2":
                print("\n--- Servicios ---")
                for idx, s in enumerate(servicios, 1):
                    estado = "Disponible" if s.disponible else "Ocupado"
                    print(f"{idx}. {s.describir_entidad()} | Tarifa: ${s.tarifa_base:.2f}/h | Estado: {estado}")

            elif opcion == "3":
                if not clientes:
                    raise ReservaInvalidaError("Debe registrar al menos un cliente primero.")

                print("\nSeleccione cliente:")
                for idx, c in enumerate(clientes, 1):
                    print(f"{idx}. {c.describir_entidad()}")
                c_idx = int(input("Número de cliente: ")) - 1

                print("\nSeleccione servicio:")
                for idx, s in enumerate(servicios, 1):
                    estado = "Disponible" if s.disponible else "Ocupado"
                    print(f"{idx}. {s.describir_entidad()} ({estado})")
                s_idx = int(input("Número de servicio: ")) - 1

                duracion = float(input("Duración en horas: "))

                nueva_reserva = Reserva(clientes[c_idx], servicios[s_idx], duracion)
                nueva_reserva.procesar_reserva()
                reservas.append(nueva_reserva)

            elif opcion == "4":
                if not reservas:
                    raise ReservaInvalidaError("No hay reservas registradas para cancelar.")

                print("\nSeleccione reserva a cancelar:")
                for idx, r in enumerate(reservas, 1):
                    print(f"{idx}. {r.cliente.obtener_identificador()} - {r.servicio.obtener_identificador()} ({r.estado})")
                r_idx = int(input("Número de reserva: ")) - 1
                reservas[r_idx].cancelar_reserva()

            elif opcion == "5":
                if not reservas:
                    print("No hay reservas registradas.")
                else:
                    print("\n--- Reservas ---")
                    for idx, r in enumerate(reservas, 1):
                        print(f"{idx}. {r.cliente.describir_entidad()} | {r.servicio.describir_entidad()} | Duración: {r.duracion}h | Estado: {r.estado}")

            elif opcion == "6":
                simular_operaciones()

            elif opcion == "0":
                logging.info("Cierre normal del sistema por el usuario.")
                print("Saliendo del sistema Software FJ...")
                break

            else:
                print("Opción no válida. Intente de nuevo.")

        except (ClienteInvalidoError, ServicioInvalidoError, ReservaInvalidaError, ServicioNoDisponibleError) as e:
            logging.error(f"Error de negocio en menú: {e}")
            print(f"[Error] {e}")
        except (ValueError, IndexError) as e:
            logging.error(f"Error de entrada en menú: {e}")
            print("[Error] Entrada inválida o índice fuera de rango. Verifique los datos ingresados.")
        except Exception as e:
            logging.error(f"Error inesperado en menú: {e}")
            print(f"[Error inesperado] {e}")


if __name__ == "__main__":
    menu_interactivo()