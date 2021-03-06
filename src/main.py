#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

from connection.connection   import Connection
from PyQt4                   import QtCore, QtGui
from ui.mainWindow           import Ui_MainWindow
from ActualizarSalidasDialog import ActualizarSalidasDialog
from ActualizarVuelosDialog  import ActualizarVuelosDialog
from AgregarSalidasDialog    import AgregarSalidasDialog
from models.vuelos           import Vuelos
from models.salidas          import Salidas
from models.reservas         import Reservas
from AgregarVuelosDialog     import AgregarVuelosDialog
from about                   import About
from ReservasDialog          import ReservasDialog

class Principal (QtGui.QMainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.conn = Connection("svr")
        self.conn.open()
        print "-------------------------- Conexion OK! --------------------------\n"

        # Actualizar las reservas vencidas para que tengan el estado
        # correspondiente.
        reservas = Reservas(self.conn)
        reservasVencidas = reservas.cantidadReservasVencidas()
        if (int(reservasVencidas) > 0):
            stringo = "Se marcaron %s reservas como vencidas \ndebido a que superaron su fecha de vencimiento." % (reservasVencidas)
            qmb = QtGui.QMessageBox().information(self, "Aviso", stringo, QtGui.QMessageBox.Ok)
            reservas.actualizarReservasVencidas()

        # Creacion de la ventana principal
        self.ventana = Ui_MainWindow()
        self.ventana.setupUi(self)

        self.about = About()
        
        # Cargar vuelos en la tabla principal
        self.todosLosVuelos = Vuelos(self.conn)
        self.todosLosVuelos.loadAll()
        self.ventana.tablaVuelos.setModel(self.todosLosVuelos.model)

        # Cargar salidas en la tabla principal
        self.todasLasSalidas = Salidas(self.conn)
        self.todasLasSalidas.loadByDate(self.ventana.calendarioVuelos.selectedDate().toString("yyyy-MM-dd"))
        self.ventana.tablaSalidas.setModel(self.todasLasSalidas.model)

        # Creacion de la ventana para la creaci�n de vuelos
        self.ventanaAltaVuelos = AgregarVuelosDialog(parent = self, conn = self.conn)

        # Creacion de la ventana para la actualizacion de los vuelos
        self.ventanaActualizacionVuelos = ActualizarVuelosDialog(parent = self, conn = self.conn)

        # Creacion del dialog ventana para la alta de las salidas.
        self.ventanaAgregarSalidas = AgregarSalidasDialog(parent = self, conn = self.conn)

        # Creacion del dialog ventana para la actualizacion de las salidas
        self.ventanaActualizacionSalida = ActualizarSalidasDialog(parent = self, conn = self.conn)

        # Creaci�n del dialog de ventana de reservas
        self.ventanaReservas = ReservasDialog(parent = self, conn = self.conn)

        # Signals de los botones de la interface del sistema
        self.connect(self.ventana.btnVuelos,              QtCore.SIGNAL('clicked()'), self.mostrarTabVuelos)
        self.connect(self.ventana.btnAgregarVuelo,        QtCore.SIGNAL('clicked()'), self.mostrarAltaVuelos)
        self.connect(self.ventana.btnModificarVuelo,      QtCore.SIGNAL('clicked()'), self.mostrarActualizacionVuelos)
        self.connect(self.ventana.btnEliminarVuelo,       QtCore.SIGNAL('clicked()'), self.eliminarVuelo)
        self.connect(self.ventana.btnInstanciasVuelos,    QtCore.SIGNAL('clicked()'), self.mostrarTabInstVuelos)
        self.connect(self.ventana.btnAgregarInstVuelos,   QtCore.SIGNAL('clicked()'), self.mostrarAltaInstanciasVuelos)
        self.connect(self.ventana.btnModificarInstVuelos, QtCore.SIGNAL('clicked()'), self.mostrarActualizacionInstanciasVuelos)
        self.connect(self.ventana.btnEliminarInstVuelos,  QtCore.SIGNAL('clicked()'), self.eliminarInstanciaVuelo)
        self.connect(self.ventana.tablaSalidas,           QtCore.SIGNAL('doubleClicked(const QModelIndex &)'), self.mostrarReservas)
        self.connect(self.ventana.calendarioVuelos,       QtCore.SIGNAL('selectionChanged()'), self.mostrarSalidas)
        self.connect(self.ventana.actionAbout,            QtCore.SIGNAL('triggered()'), self.showAbout)
        self.connect(self.ventana.actionExit,             QtCore.SIGNAL('triggered()'), self.quit)

        # DIEGOOOOOOOOO
        # self.connect(self.ventana.menuba.wtf("WTF goes here?"), QtCore.SIGNAL( "WTF goes here?" ), sys.exit(app.exec_()))

    #--------------------------------------------------------------------------#
    def refreshTableViews(self):
        self.todosLosVuelos.loadAll()
        self.ventana.tablaVuelos.setModel(self.todosLosVuelos.model)
        selectedDate = self.ventana.calendarioVuelos.selectedDate().toString("yyyy-MM-dd")
        self.todasLasSalidas.loadByDate(selectedDate)
        self.ventana.tablaSalidas.setModel(self.todasLasSalidas.model)





    # VUELOS ###################################################################

    #--------------------------------------------------------------------------#
    def mostrarTabVuelos(self):
        self.ventana.stackedWidget.setCurrentIndex(1)
        self.refreshTableViews()

    #--------------------------------------------------------------------------#
    def mostrarAltaVuelos(self):
        self.ventanaAltaVuelos.exec_()
        self.refreshTableViews()

    #--------------------------------------------------------------------------#
    def mostrarActualizacionVuelos(self):
        # compruebo que haya alg�n item seleccionado
        if (self.ventana.tablaVuelos.selectedIndexes()):
            index = self.ventana.tablaVuelos.selectionModel().currentIndex().row()
            vuelo_id = self.todosLosVuelos.getModel().record(index).value(0).toString()
            origen   = self.todosLosVuelos.getModel().record(index).value(1).toString() 
            destino  = self.todosLosVuelos.getModel().record(index).value(2).toString()  
            self.ventanaActualizacionVuelos.setData(vuelo_id, origen, destino)
            self.ventanaActualizacionVuelos.exec_()
            self.refreshTableViews()

    #--------------------------------------------------------------------------#
    def eliminarVuelo(self):
        index = self.ventana.tablaVuelos.selectionModel().currentIndex().row()
        if index >= 0:
            reply = QtGui.QMessageBox.question(self, "Mensaje","�Est� seguro que desea eliminar ese registro?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.Yes:
                vuelo_id = self.todosLosVuelos.getModel().record(index).value(0).toString()
                print "Selected index: ", index, "ID: ", vuelo_id

                # Con el id del vuelo, eliminar todas las salidas con ese id de vuelo.
                modelo_reservas = Reservas(self.conn)
                salidas  = Salidas(self.conn)
                salidas.loadAllFlightInstances(vuelo_id)
                modelo_salidas = salidas.getModel()

                for salida in range(modelo_salidas.rowCount()):
                    # Borrar todas las reservas asociadas a esta instancia de vuelo.
                    diahora_sale = modelo_salidas.record(salida).value(1).toString()
                    print "Eliminando reservas de la instancia de de vuelo: ", vuelo_id, diahora_sale
                    modelo_reservas.deleteAll(vuelo_id, diahora_sale)

                print "Eliminando todas las instancias de este vuelo..."
                self.todasLasSalidas.deleteAll(vuelo_id)
                print "Eliminando el vuelo..."
                self.todosLosVuelos.delete(vuelo_id)
                print "Vuelo eliminado exitosamente."
                self.refreshTableViews()





    # SALIDAS ##################################################################

    #--------------------------------------------------------------------------#
    def mostrarTabInstVuelos(self):
        # Al mostrar devuelta el tab de las instancias de vuelos, volver a 
        # cargar los datos en la tabla.
        self.ventana.stackedWidget.setCurrentIndex(0)
        self.refreshTableViews()

    #--------------------------------------------------------------------------#
    def mostrarAltaInstanciasVuelos(self):
        self.ventanaAgregarSalidas.setData(self.ventana.calendarioVuelos.selectedDate())
        self.ventanaAgregarSalidas.exec_()
        self.refreshTableViews()

    #--------------------------------------------------------------------------#
    def mostrarActualizacionInstanciasVuelos(self):
        # compruebo que haya alg�n item seleccionado
        if(self.ventana.tablaSalidas.selectedIndexes()):
            index          = self.ventana.tablaSalidas.selectionModel().currentIndex().row()
            vuelo_id       = self.todasLasSalidas.getModel().record(index).value(0).toString()
            diahora_sale   = self.todasLasSalidas.getModel().record(index).value(1).toString()
            diahora_llega  = self.todasLasSalidas.getModel().record(index).value(2).toString()
            estado         = self.todasLasSalidas.getModel().record(index).value(3).toString()
            self.ventanaActualizacionSalida.setData(vuelo_id, diahora_sale, diahora_llega, estado)
            self.ventanaActualizacionSalida.exec_()
            self.refreshTableViews()

    #--------------------------------------------------------------------------#
    def eliminarInstanciaVuelo(self):
        # Obtener el id de la salida seleccionada
        index        = self.ventana.tablaSalidas.selectionModel().currentIndex().row()
        if index >=0:
            reply = QtGui.QMessageBox.question(self, "Mensaje","�Est� seguro que desea eliminar ese registro?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
            if reply == QtGui.QMessageBox.Yes:
                vuelo_id     = self.todasLasSalidas.getModel().record(index).value(0).toString()
                diahora_sale = self.todasLasSalidas.getModel().record(index).value(1).toString()

                # Borrar todas las reservas asociadas a esta instancia de vuelo.
                reservas = Reservas(self.conn)
                reservas.deleteAll(vuelo_id, diahora_sale)

                # Ahora que las restricciones de clave foraneas estan satisfechas, 
                # efectivamente borrar la instancia de vuelo.
                self.todasLasSalidas.delete(vuelo_id, diahora_sale)
                print "Instancia de vuelo eliminada exitosamente."
                self.refreshTableViews()


    def mostrarSalidas(self):
        self.refreshTableViews()
        
        
    


    # RESERVAS #################################################################

    def mostrarReservas(self):
        index      = self.ventana.tablaSalidas.selectionModel().currentIndex().row()
        vuelo_id   = self.todasLasSalidas.getModel().record(index).value(0).toString()
        dia_y_hora = self.todasLasSalidas.getModel().record(index).value(1).toString()
        self.ventanaReservas.setData(vuelo_id, dia_y_hora)
        self.ventanaReservas.exec_()

        
        
        
    # AUXILIARES ###############################################################
    
    def showAbout(self):
        self.about.exec_()
    
    def quit(self):
        sys.exit()
    
    
    
#------------------------------------------------------------------------------#
def main():
        app = QtGui.QApplication (sys.argv)
        ventana = Principal()
        ventana.show()
        sys.exit(app.exec_())

if __name__ == '__main__':
    main()
