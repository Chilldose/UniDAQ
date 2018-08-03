#This class provides usefull functions for gernerall purposes
#Class functions:
#create_new_file,

#IO-functions
# open_file,
# close_file,
# flush_to_file,
# close_file,
# read_from_file,
# write_to_file,
#
#Ramping
# ramp_voltage

import os, sys, os.path, re
from time import sleep
import time
import threading
import logging, json
from PyQt5 import QtCore
import numpy as np
from numpy.linalg import solve, norm, det, qr, inv
import datetime
import pyqtgraph as pg
import VisaConnectWizard
from PyQt5.QtWidgets import QApplication
#from __future__ import print_function # Needed for the rtd functions that its written in 3

l = logging.getLogger(__name__)
lock = threading.Lock()

class help_functions:
    """Helpfull function is a multipurpose class with a variety of function and tasks.
    It contains functions regarding error handling an file generation as well as generating ramps (e.g. for bias ramps)
    For more information see he docs for the functions itself"""

    def __init__(self ):
        pass


    def write_init_file(self, name, data, path = ""):
        """
        This function writes init files for devices and default files

        :param name: Name of the file to be written to
        :param data: Data in Dict format
        :param path: Path where to write
        :return:
        """

        # find the resource and exclude it from the file
        data = data.copy()

        #Removes the Visa resource if needed
        try:
            data.remove("Visa_Resource")
        except:
            pass

        if os.path.isfile(os.path.abspath(str(path) + str(name.split(".")[0]) + ".json")):

            os.remove(os.path.abspath(path + str(name.split(".")[0]) + ".json"))
            #directory = path[:len(path)-len(path.split("/")[-1])]
            file = self.create_new_file(str(name.split(".")[0]), path, os_file=False, suffix=".json")

            json.dump(data, file, indent=4, ensure_ascii=False)

            self.close_file(file)

        elif not os.path.isfile(os.path.abspath(path + str(name.split(".")[0]) + ".json")):

            #directory = path[:len(path) - len(path.split("/")[-1])]

            file = self.create_new_file(str(name.split(".")[0]), path, os_file=False, suffix=".json")

            json.dump(data, file, indent=4, ensure_ascii=False)

            self.close_file(file)


            # Debricated
            #for items in data.items():
            #    if type(items[1]) != type([]):
            #        string = str(items[0]) + " = \"" + str(items[1]) + "\"\n"
            #        os.write(file, str(string))
            #    else:
            #        string = str(items[0]) + " = \""
            #        for i in items[1]:
            #            string += str(i).strip("'").strip("[").strip("]") + ","
            #        string = string[:-1]
            #        string += "\"\n"
            #        print string
            #        os.write(file, string)



        else:
            return -1

    # This function works as a decorator to measure the time of function to execute
    def timeit(self, method):
        """
        Intended to be used as decorator for functions. It returns the time needed for the function to run

        :param method: method to be timed
        :return: time needed by method
        """

        def timed(*args, **kw):
            start_time = time.time()
            result = method(*args, **kw)
            end_time = time.time()

            exce_time = end_time-start_time

            return result, exce_time

        return timed # here the memberfunction timed will be called

    # These functions are for reading and writing to files------------------------------------
    #-----------------------------------------------------------------------------------------

    # This function works as a decorator to raise errors if python interpretor does not do that automatically
    def raise_exception(self, method):
        """
        Intended to be used as decorator for pyQt functions in the case that errors are not correctly passed to the python interpret
        """
        def raise_ex(*args, **kw):
            try:
                #Try running the method
                result = method(*args, **kw)
            # raise the exception and print the stack trace
            except Exception as error:
                print("Some error occured in the function " + str(method.__name__) +". With Error:", repr(error))  # this is optional but sometime the raise does not work
                raise  # this raises the error with stack backtrack
            return result

        return raise_ex# here the memberfunction timed will be called

        # This function works as a decorator to raise errors if python interpretor does not do that automatically

    def run_with_lock(self, method):
        """
        Intended to be used as decorator for functions which need to be threadsave. Warning: all functions acquire the same lock, be carefull.


        """
        def with_lock(*args, **kw):
            try:
                # Try running the method
                with lock:
                    l.debug("Lock acquired by program: " + str(method.__name__))
                    result = method(*args, **kw)
                l.debug("Lock released by program: " + str(method.__name__))
            # raise the exception and print the stack trace
            except Exception as error:
                print("A lock could not be acquired in "  + str(method.__name__) +". With Error:", repr(error)) # this is optional but sometime the raise does not work
                raise  # this raises the error with stack backtrace
            return result

        return with_lock  # here the memberfunction timed will be called

    # Creates a new file
    def create_new_file(self, filename="default.txt", filepath = "default_path", os_file=True, suffix = ".txt"):
        """
        Simply creates a file

        :param filename:
        :param filepath:
        :param os_file:
        :param suffix:
        :return:
        """

        counter = 0

        if filepath == "default_path":
            filepath = ""
        elif filepath == "":
            pass
        else:
            filepath += "/"

        filename += str(suffix)

        #First check if Filename already exists, when so, add a counter to the file.
        if os.path.isfile(os.path.abspath(filepath+filename)):
            print("Warning filename " + str(filename) + " already exists!")
            l.warning("Warning filename " + str(filename) + " already exists!")
            filename = filename[:-4] + "_" + str(counter) + ".txt" # Adds sufix to filename
            while os.path.isfile(os.path.abspath(filepath+filename)):  # checks if file exists
                filename = filename[:-5] + str(counter)  + ".txt"  # if exists than change the last number in filename string
                counter += 1
            print("Filename changed to " + filename + ".")
            l.info("Filename changed to " + filename + ".")

        if os_file:
            fd = os.open(os.path.abspath(filepath+filename), os.O_WRONLY | os.O_CREAT) # Creates the file
        else:
            fd = open(os.path.abspath(filepath+filename), "w")

        l.info("Generated file: " + str(filename))
        print("Generated file: " + str(filename))

        return fd

    # Opens a file for reading and writing
    def open_file(self, filename="default.txt", filepath = "default_path"):
        """
        Just opens a file and returns the file pointer

        :return: File
        """

        if filepath == "default_path":
            filepath = ""

        try:
            fd = open(filepath + filename, 'r+') #Opens file for reading and writing
            return fd
        except IOError:
            print(str(filepath + filename) + " is not an existing file.")


    # Closes a file (just needs the file pointer)
    def close_file(self, file):
        """
        Closed the file specified in param file

        """
        try:
            try:
                os.close(file)
            except:
                file.close()
        except GeneratorExit:
            print("Closing the file: " + str(file) + " was not possible")
        except:
            print("Unknown error occured, while closing file " + str(file) + "Error: ", sys.exc_info()[0])

    # This flushes a string to a file
    def flush_to_file(self, file, message):
        """
        Flushes data to a opend file
        Only strings or numbers allowed, Lists will work too but may cause data scrambling
        Only use this with created files from function 'create_new_file'
        """
        os.write(file, str(message)) #Writes the message to file
        os.fsync(file) # ensures that the data is written on HDD

    def write_to_file(self, content, filename="default.txt", filepath = "default_path"):
        """
        This writes content to a file. Be aware, input must be of type 'list' each entry containing the information of one line
        """

        file = self.open_file(filename, filepath)

        try:
            for line in content:
                file.write(str(line))
        except IOError:
            print("Writing to file " + filename + " was not possible")
        except:
            print("Unknown error occured, while writing to file " + str(filename) + "Error: ", sys.exc_info()[0])

        self.close_file(file)

    def read_from_file(self, filename="default.txt", filepath = "default_path"):
        """
        Gives you the content of the file in an list, each list entry is one line of the file (datatype=string)
        Warning: File gets closed after reading
        """

        file = self.open_file(filename, filepath)

        try:
            return file.readlines()
        except IOError:
            print("Could not read from file.")
            return []
        except:
            print("Unknown error occured, while reading from file " + str(filename) + "Error: ", sys.exc_info()[0])

        self.close_file(file)

    # These functions are for reading and writing to files------------------------------------
    # -------------------------------------------------------------------------------------end

    def ramp_voltage_job(self, queue, resource, order, voltage_Start, voltage_End, step, wait_time = 0.2, complience=100e-6):
        """
        Only use this function for simple ramping for the main, never inside a measurement!!!
        """
        job = {"Measurement": {"ramp_voltage": {"Resource": resource,
                                "Order": order,
                                "StartVolt": voltage_Start,
                                "EndVolt": voltage_End,
                                "Steps": step,
                                "Wait": wait_time,
                                "Complience": complience}}}
        queue.put(job)

    # These function is for ramping up or down (not final)
    def ramp_voltage(self, VisaResource, instrument, order_code, max_value, ramp_steps, time_to_wait, ramp_up=True):
        """
        Deprecated
        This function ramps a value by sending commands after a timeout. Usage, ramping voltage for a device

        :param VisaResource: Device which gets the commands
        :param instrument:
        :param order_code:  Code which has to be send
        :param max_value: Maximum value from where to be ramped
        :param ramp_steps: Stepssize
        :param time_to_wait: waitingtime
        :param ramp_up: Whether or not to ramp from abs up or down
        :return:
        """
        print("Warning old ramp function was used!!!")

        step_size = round(max_value / ramp_steps, 0)
        instrument_to_write = VisaResource.myInstruments[instrument]

        for voltage in range(ramp_steps + 1):

            if ramp_up:
                VisaResource.write(instrument_to_write, str(order_code) + " " + str(voltage * step_size))
                sleep(time_to_wait)
            else:
                VisaResource.write(instrument_to_write, str(order_code) + " " + str((ramp_steps - voltage) * step_size))
                sleep(time_to_wait)

        if ramp_up:
            VisaResource.write(instrument_to_write, str(order_code) + " " + str(max_value))

        else:
            VisaResource.write(instrument_to_write, str(order_code) + " " + str(0))
        # These function is for ramping up or down


    def int2dt(self, ts, ts_mult = 1e3):
        """
        Convert seconds value into datatime struct which can be used for x-axis labeeling
        """
        return datetime.datetime.utcfromtimestamp(float(ts) / ts_mult)


    def get_timestring_from_int(self, time_array, format = "%H:%M:%S"):
        """
        Converts int time to timestring
        """
        list = []
        for value in time_array:
            list.append((value, self.int2dt(value,1).strftime(format)))
        return list


    def get_thicks_for_timestamp_plot(self, time_array, max_number_of_thicks = 10, format = "%H:%M:%S"):
        """
        This gives back a list of tuples for the thicks
        """
        final_thicks = []
        if len(time_array) <= max_number_of_thicks:
            final_thicks = self.get_timestring_from_int(time_array, format)
        else:
            length = len(time_array)
            delta = int(length/max_number_of_thicks)
            for i in range(0, length, delta):
                final_thicks.append((time_array[i], self.int2dt(time_array[i],1).strftime(format)))
        return final_thicks


    class CAxisTime(pg.AxisItem):
        """Over riding the tickString method by extending the class"""

            # @param[in] values List of time.
            # @param[in] scale Not used.
            # @param[in] spacing Not used.
        def tickStrings(self, values, scale, spacing):
            """Generate the string labeling of X-axis from the seconds value of Y-axis"""
            # sending a list of values in format "HH:MM:SS.SS" generated from Total seconds.
            return [(self.int2dt(value).strftime("%H:%M:%S.%f"))[:-4] for value in values]

        def int2dt(ts, ts_mult=1e3):
            """Convert seconds value into datatime struct which can be used for x-axis labeeling"""
            return (datetime.utcfromtimestamp(float(ts) / ts_mult))

hf = help_functions()

class newThread(threading.Thread):  # This class inherite the functions of the threading class
    '''Creates new threads easy, it needs the thread ID a name, the function/class,
    which should run in a seperated thread and the arguments passed to the object'''

    def __init__(self, threadID, name, object__, *args):  # Init where the threadID and Thread Name are defined
        """
        :param threadID: ID the thread should have
        :param name: Give the thread a name you want
        :param object__: The object which should run in the new thread
        :param args: Arguments passed to object__
        """

        threading.Thread.__init__(self)  # Opens the threading class

        self.threadID = threadID
        self.name = name
        self.object__= object__
        self.args = args

    def run_process(self, object__, args): # Just for clarification, not necessary.
        """
        """
        return object__(*args)

    def run(self):
        """Starts running the thread"""
        print ("Starting thread: " + self.name) # run() is a member function of Thread() class. This will be called, when object thread will be started via thread.start()
        l.info("Starting thread: " + self.name)
        self.object__ = self.run_process(self.object__, self.args)

    def get(self):
        '''returns the Object'''
        return self.object__

class newThread_(QtCore.QThread):  # This class inherite the functions of the threading class
    '''Creates new threads easy, it needs the thread ID, a name, the function/class, which should run in a seperated thread
    This is the same thing like newThread but instead QTCore modules are used.'''

    def __init__(self, threadID, name, object__, *args):  # Init where the threadID and Thread Name are defined

        QtCore.QThread.__init__(self)  # Opens the threading class

        self.threadID = threadID
        self.name = name
        self.object__= object__
        self.args = args

    def run_process(self, object__, args): # Just for clarification, not necessary.
        return object__(*args)

    def run(self):
        print ("Starting thread: " + self.name) # run() is a member function of Thread() class. This will be called, when object thread will be started via thread.start()
        l.info("Starting thread: " + self.name)
        self.object__ = self.run_process(self.object__, self.args)

    @staticmethod
    def get():
        '''returns the Object''' # Not working, do not use
        newThread_.object__()

class LogFile:
    """
    This class handles the Logfile for the whole framework
    """

    def __init__(self, logging_level = "debug"):
        """
        Initiates the logfile with the logging level
        :param logging_level: None, debug, info, warning, error critical
        """

        self.LOG_FORMAT = "%(levelname)s %(asctime)s in function %(funcName)s - %(message)s"
        self.file_PATH = os.path.normpath(os.path.realpath(__file__)[:-30] + "/Logfiles/QTC_Logfile.log") # Filepath to Logfile directory
        self.file_directory = os.path.normpath(os.path.realpath(__file__)[:-30] + "/Logfiles")
        self.logging_level = logging_level
        self.log_LEVELS = {"NOTSET": 0, "DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}

        self.welcome_string =  "\n" \
                               "\t\t\t\t\t\t\t\t  __         ______     ______     ______   __     __         ______           ______     ______   ______\n  \
                               /\ \       /\  __ \   /\  ___\   /\  ___\ /\ \   /\ \       /\  ___\         /\  __ \   /\__  _\ /\  ___\ \n   \
                              \ \ \____  \ \ \/\ \  \ \ \__ \  \ \  __\ \ \ \  \ \ \____  \ \  __\         \ \ \/\_\  \/_/\ \/ \ \ \____ \n  \
                                \ \_____\  \ \_____\  \ \_____\  \ \_\    \ \_\  \ \_____\  \ \_____\        \ \___\_\    \ \_\  \ \_____\ \n \
                                  \/_____/   \/_____/   \/_____/   \/_/     \/_/   \/_____/   \/_____/         \/___/_/     \/_/   \/_____\n\n\n"

        self.get_logging_level()
        try:
            os.remove(self.file_PATH) # IS needed, because sometimes other modules like the visa modules would override the file and all logs are lost, so the log file is in appending mode and no data loss.
        except Exception as e:
            print ("Old Logfile could not be deleted: " + str(e))
        # Check if the folder already exists or create the folder
        if os.path.isdir(self.file_directory):
            logging.basicConfig(filename=self.file_PATH, level=self.logging_level, format = self.LOG_FORMAT, filemode= 'a') # Overrides the old file (this is just for initialization)
        else:
            os.makedirs(self.file_directory)
            logging.basicConfig(filename=self.file_PATH, level=self.logging_level, format = self.LOG_FORMAT, filemode= 'a') # Overrides the old file (this is just for initialization)


        # Create a logger Object
        self.LOG = logging.getLogger()

        # Print welcome message
        self.LOG.critical(self.welcome_string)


    #Simply changes the string input to a int for the logging level
    def get_logging_level(self):
        ''' Checks the logging level input. If it is a string -> convert. Otherwise, do nothing'''
        if type(self.logging_level) == type("string"):
            self.logging_level=self.log_LEVELS.get(self.logging_level.upper(), "DEBUG")
        else:
            pass

class Framework:
    """
    Generall class for handling all Framework related tasks, like updating the GUI etc.
    """

    def __init__(self, values_from_GUI):
        """
        :param values_from_GUI: A tuple of (list of functions, udate intervall)
        """

        self.functions, self.update_interval = values_from_GUI()
        self.timer = None

    def start_timer(self):  # Bug timer gets not called due to a lock somewhere else
        """
        Simply starts the timer

        :return: timer
        """
        l.info("Framework initialized")
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update_)
        timer.start(self.update_interval)
        self.timer = timer

        return timer

    def update_(self):
        """
        Periodically updates the functions in self.functions list

        :return: None
        """
        #start = time.time()
        for function in self.functions:
            try:
                function()
            except:
                l.error("Could not update framework " + function)
        #end = time.time()
        #print end - start

class transformation_old:

    def vector_transform(self,v,T):
        '''This function transform one vector into the basis of another'''
        return T.dot(v)


    def transformation_matrix(self, a, b):
        '''Calculates the transformation matrix of the system.
        Via the equation T = P^-1 Q where P and Q are comming from the linear system s*T + V0 = v
        a and must  be the linear hull (or simple three linear independent vecotrs)'''

        P = np.transpose(np.array([[a[1][0]-a[0][0],a[2][0]-a[0][0]],
                                  [a[1][1]-a[0][1],a[2][1]-a[0][1]]]))
                     #[a[1][2]-a[0][2],a[2][2]-a[0][2]]]))

        print(P.shape)

        Pinvert = inv(P)

        Q = np.transpose(np.array([ [b[1][0]-b[0][0],b[2][0]-b[0][0]],
                                    [b[1][1]-b[0][1],b[2][1]-b[0][1]],
                                    [b[1][2]-b[0][2],b[2][2]-b[0][2]]

                                    ]))

        print(Q.shape)
        #T = solve(P, Q)

        T = Pinvert.dot(Q)

        print(T)

        #print T.dot(np.transpose(a)[1])

        #V0 = np.transpose(b)[1] - np.dot(np.transpose(a)[1],T)

        #print V0

        return

    def linear_dependency(self, x):
        '''Calculates if the matrizes a and b are linear independet.
        a and b must be matrizes of type np.array([a1,a2,a3]), where ai are the corresponding linearhull.
        '''

        # Test linear dependency
        detx = det(x)
        if detx != 0:
            return True
        else:
            return False

    def qr_factorisation(self,x):
        '''Calculates the qr factorisation of a matrix (linear indenendecy is requiered)
        Basically it just calculates a Orthogonal matrix q and a upper triangula matrix r.
        A=Q*R is the basic principal behind it.'''

        q,r = qr(x)
        return q

    def renorm(self,x):
        '''Renormalise the basis vektors of a matrix'''
        for i in range(len(x)):
            x[i]=x[i]/norm(x[i])

        return x

class transformation:
    """Class which handles afine transformations in 3 dimensions for handling sensor to jig coordinate systems"""

    @hf.raise_exception
    def transformation_matrix(self, s1, s2, s3, t1, t2 ,t3):
        """Calculates the transformation matrix of the system.
        Via the equation T = P^-1 Q where P and Q are coming from the linear system s*T + V0 = v
        si are the corresponding vectors (coordinates) in the sensor system, ti are those from the table system.
        They must be numpy arrays.
        """

        s1 = np.array(s1)
        s2 = np.array(s2)
        s3 = np.array(s3)
        t1 = np.array(t1)
        t2 = np.array(t2)
        t3 = np.array(t3)

        Q = np.array([
                    [t2[0] - t1[0], t2[1] - t1[1], t2[2] - t1[2]],
                    [t3[0] - t1[0], t3[1] - t1[1], t3[2] - t1[2]]
        ])

        P = np.array([
                    [s2[0] - s1[0], s2[1] - s1[1]],
                    [s3[0] - s1[0], s3[1] - s1[1]]
        ])


        try:
            # Invert the P matrix
            Pinv = inv(P)

            # Build the dot product
            T = np.dot(Pinv, Q)

            # Offset
            V0 = np.subtract(t2,np.transpose(s2[0:2]).dot(T))
        except Exception as e:
            l.error("An error occured during the transformation with error: " + str(e))
            return -1, -1

        return T, V0

    def vector_trans(self, v, T, V0):
        """This function transforms a Vector from the sensor system to the table system by vs*T+V0=vt"""
        v = np.array(v)
        return np.add(v[0:2].dot(T),V0)

class measurement_job_generation:
    """This class handles all measurement generation items"""

    def __init__(self, main_variables, queue_to_measurement_event_loop):
        """

        :param main_variables: Simply the state machine variables ('defaults')
        :param queue_to_measurement_event_loop:
        """
        self.variables = main_variables["Defaults"]
        self.queue_to_measure = queue_to_measurement_event_loop
        self.final_job = {}

    def generate_job(self, additional_settings_dict):
        '''
        This function handles all the work need to be done in order to generate a job
        :param additional_settings_dict: If any additional settings are in place
        '''

        self.final_job = additional_settings_dict


        header = "# Measurement file: \n " \
                      "# Project: " + self.variables["Current_project"]  + "\n " \
                      "# Sensor Type: " + self.variables["Current_sensor"]  + "\n " \
                      "# ID: " + self.variables["Current_filename"] + "\n " \
                      "# Operator: " + self.variables["Current_operator"] + "\n " \
                      "# Date: " + str(time.asctime()) + "\n\n"

        IVCV_dict = self.generate_IVCV("") # here additional header can be added
        strip_dict = self.generate_strip("")

        if IVCV_dict:
            self.final_job.update({"IVCV": IVCV_dict})
        if strip_dict:
            self.final_job.update({"stripscan": strip_dict})

        # Check if filepath is a valid path
        if self.variables["Current_filename"] and os.path.isdir(self.variables["Current_directory"]):
            self.final_job.update({"Header": header})
            self.queue_to_measure.put({"Measurement": self.final_job})
            print ("Sendet job: " + str({"Measurement": self.final_job}))
        else:
            l.error("Please enter a valid path and name for the measurement file.")
            print ("Please enter a valid path and name for the measurement file.")

    def generate_IVCV(self, header):
        '''
        This function generates all that has to do with IV or CV
        :param header: An additional header
        :return: the job dictionary
        '''
        final_dict = {}
        file_header = header

        if self.variables["IV_measure"][0]:
            file_header += "voltage[V]".ljust(24) +  "current[A]".ljust(24)
        if self.variables["CV_measure"][0]:
            file_header += "voltage[V]".ljust(24) + "capacitance[F]".ljust(24)

        file_header += "temperature[deg]".ljust(24) + "humidity[rel%]".ljust(24)

        final_dict.update({"header": file_header})

        if self.variables["IV_measure"][0]:
            values = self.variables["IV_measure"]
            final_dict.update({"IV": {"StartVolt": 0, "EndVolt": values[1], "Complience": str(values[2])+ "e-6", "Steps": values[3]}})

        if self.variables["CV_measure"][0]:
            values = self.variables["CV_measure"]
            final_dict.update({"CV": {"StartVolt": 0, "EndVolt": values[1], "Complience": str(values[2])+ "e-6", "Steps": values[3]}})

        if len(final_dict) > 1:
            return final_dict
        else:
            return {} # If the dict consits only of one element (only the header)

    def generate_strip(self, header):
        '''
        This function generate all tha has to do with strip scans
        :param header: Additional header
        :return: strip job dictionary
        '''

        final_dict = {}
        all_measurements = ["Rint", "Istrip", "Idiel", "Rpoly","Cac", "Cint", "Idark", "Cback", "CintAC"] # warning if this is not included here no job will generated. is intentional

        def generate_dict(values):
            ''' Generates a simple dict for strip scan measurements'''
            if values[0]: # Checks if the checkbox is true or false, so if the measurement should be condcuted or not
                return {"measure_every": values[1], "start_strip": values[2], "end_strip": values[3]}
            else:
                return {}

        # First check if strip scan should be done or not
        if self.variables["Stripscan_measure"][0]:
            final_dict.update({"StartVolt": 0, "EndVolt": self.variables["Stripscan_measure"][1], "Complience": str(self.variables["Stripscan_measure"][2])+ "e-6", "Steps": self.variables["Stripscan_measure"][3]})

            for elemets in all_measurements:
                dict = generate_dict(self.variables[elemets + "_measure"])
                if dict:
                    final_dict.update({elemets: dict})

        final_dict.update({"Additional Header": header})

        if len(final_dict) > 2:
            return final_dict
        else:
            return {} # If the dict consits only of one element (only the header)


class table_control_class:
    '''This class handles all interactions with the table. Movement, status etc.
    This class is designed to be running in different instances.'''

    def __init__(self, main_variables, device, queue_to_GUI, shell):
        """

        :param main_variables: Defaults dict
        :param device: The VISA device object
        :param queue_to_GUI:
        :param shell: The UniDAQ shell object
        """
        self.variables = main_variables["Defaults"]
        self.device = device
        self.table_ready = self.variables["table_ready"]
        self.queue = queue_to_GUI
        self.vcw = VisaConnectWizard.VisaConnectWizard()
        self.shell = None

        try:
            self.visa_resource = self.device["Visa_Resource"]
            self.table_ready = True
        except:
            print ("Warning table control could not be initialized!")
            self.table_ready = False
            self.queue.put({"RequestError": "Table seems not to be connected!"})
            l.error("Table control could not be initialized!")
        self.zmove = self.variables["height_movement"]


    def __build_command(self, order, values , command_order = 1):
        '''
        This function builds the correct orders together, it always returns a list,
        if a order needs to be sended several times with different values
        :param order: The actual command
        :param values: List of values which need to be send alongside order
        :param command_order: If the commands in the list should be sended reversed or not (-1, 1)

        '''
        if values:
            if type(values) != list: # ensures we have a list
                values_list = [values]
            else:
                values_list = values

            full_command_list = []
            if int(command_order) == 1:
                for item in values_list:
                    full_command_list.append(str(order)+ " " + str(item).strip())
                return full_command_list

            elif int(command_order) == -1:
                for item in values_list:
                    full_command_list.append(str(item) + " " + str(order))
                return full_command_list

            else:
                l.error("Something went wrong with the building of the table command!")
        else:
            if type(order) != list: # ensures we have a list
                return [order]
            else:
                return order

    def get_current_position(self):
        '''Queries the current position of the table and writes it to the state machine'''
        if self.table_ready:
            while True: # Loop as long as there is a valid position from the corvus
                try:
                    command = self.__build_command(self.device["get_position"], "", self.device["command_order"])
                    string = self.vcw.query(self.visa_resource, command[0],self.device.get("execution_terminator", "")).strip()
                    list = re.split('\s+', string)[:3]
                    self.device["x_pos"] = float(list[0])
                    self.device["y_pos"] = float(list[1])
                    self.device["z_pos"] = float(list[2])
                    return [float(i) for i in list]
                except:
                    l.error("The corvus has replied with a non valid position string: " + str(string))

    def check_if_ready(self, timeout = 0, maxcounter = -1):
        '''
        This function checks if the movement of the table is done or not
        :param timeout: Timeout how long to wait between the attempts
        :param maxcounter: How often does the function try to get an answer, -1 infinite
        :return: 0 if ok error if not
        '''
        # Alot of time can be wasted by the timeout of the visa read order
        ready_command = self.__build_command(self.device["all_done"], "", self.device["command_order"])
        counter = 0 # counter how often the read attempt will be carried out
        cal_not_done = True
        self.vcw.write(self.visa_resource, ready_command[0], self.device.get("execution_terminator", ""))
        while cal_not_done:
            done = self.vcw.read(self.visa_resource)

            if maxcounter != -1:
                counter += 1
                if counter > maxcounter:
                    cal_not_done = False #exits the loop after some attempts

            if float(done) == -1: # case when corvus is busy and does not respond to anything
                pass

            elif float(done) == 1: # motors are in movement
                self.vcw.write(self.visa_resource, ready_command[0], self.device.get("execution_terminator", "")) # writes the command again

            elif float(done) == 2: # joystick active
                cal_not_done = False
                return {"RequestError": "Joystick of table control is active."}

            elif float(done) == 4: # joystick active
                cal_not_done = False
                return {"RequestError": "Table control is not switched on."}

            elif float(done) > 4: # joystick active
                cal_not_done = False
                return {"RequestError": "The table control reported an unknown error, with errorcode: " + str(done)}

            elif float(done) == 0: # when corvus is read again
                self.get_current_position()
                cal_not_done = False
                return 0

            QApplication.processEvents() # Updates the GUI, maybe after some iterations

            sleep(timeout)

    def initiate_table(self):
        '''
        This function triggers the table initiation

        :return: 0 if ok error if not
        '''
        if self.table_ready and not self.variables["table_is_moving"]:
            self.variables["table_is_moving"] = True
            commands = self.__build_command(self.device["calibrate_motor"], "", self.device["command_order"])
            for order in commands:
                self.vcw.write(self.visa_resource, order, self.device.get("execution_terminator", ""))
                errorcode = self.check_if_ready()
                if errorcode == 0:
                        pos = self.get_current_position()
                        if commands[0] == order:
                            self.device["table_xmin"] = float(pos[0])
                            self.device["table_ymin"] = float(pos[1])
                            self.device["table_zmin"] = float(pos[2])
                        else:
                            self.device["table_xmax"] = float(pos[0])
                            self.device["table_ymax"] = float(pos[1])
                            self.device["table_zmax"] = float(pos[2])
                else:
                    return errorcode
            self.variables["table_is_moving"] = False
            return 0

    def check_position(self, desired_pos):
        '''
        This function checks if two positions are equal or not

        :param desired_pos: The position it should be
        :return: 0 if ok error if not
        '''
        new_pos = self.get_current_position()
        for i, pos in enumerate(new_pos):
            if abs(float(pos) - float(desired_pos[i])) > 0.5: # up to a half micrometer
                errorcode = {"MeasError": "Table movement failed. Position: " + str(new_pos) + " is not equal to desired position: " + str(desired_pos)}
                l.error("Table movement failed. Position: " + str(new_pos) + " is not equal to desired position: " + str(desired_pos))
                return errorcode
        return 0

    def __already_there(self, pad_file, strip, transfomation_class, T, V0):
        '''
        Checks if we are already at the strip we want to move to

        :param pad_file:
        :param strip:
        :param transfomation_class:
        :param T:
        :param V0:
        :return: True if at strip
        '''
        pos = self.get_current_position()  # table position
        pad_pos = [float(x) for x in pad_file["data"][strip][1:4]]  # where it should be in sensor system
        table_pos = transfomation_class.vector_trans(pad_pos, T, V0)  # Transforms the vektor to the right basis
        deltapos = [abs(x1 - x2) for (x1, x2) in zip(pos, table_pos)]

        for delta in deltapos:
            if delta >= 0.5:  # Checks if the position is correct in a range of 0.5 um
                return False
        return True


    def move_to_strip(self, pad_file, strip, transfomation_class, T, V0, height_movement = 800):
        '''
        Moves to a specific strip

        :param transfomation_class:
        :param height_movement: How much should the table move down
        :return: None or errorcode
        '''

        error = None
        if transformation != []:
            if not self.__already_there(pad_file, strip, transfomation_class, T, V0):
                pad_pos = pad_file["data"][strip][1:4]
                l.info("Moving to strip: {} at position {},{},{}.".format(strip, pad_pos[0], pad_pos[1], pad_pos[2]))
                table_abs_pos = transfomation_class.vector_trans(pad_pos, T, V0)
                error = self.move_to(table_abs_pos, move_down=True, lifting = height_movement)

            self.variables["current_strip"] = int(strip+1)
            return error
        else:
            return {"RequestError": "No Transformation Matrix found! Is the alignment done?"}


    def relative_move_to(self, position, move_down = True, lifting = 800):
        '''
        This function moves the table to the desired position (relative). position is a list of coordinates
        The move down parameter can prohibit a down and up movement with the move, !!!!USE WITH CARE!!!!

        :return: none or error code
        '''
        error = self.move_to(position, move_down, lifting, True)
        return error


    def move_to(self, position, move_down = True, lifting  = 800, relative_move = False):
        '''
        This function moves the table to the desired position. position is a list of coordinates
        The move down parameter can prohibits a down and up movement with the move, !!!!USE WITH CARE!!!!

        :return: None or errorcode
        '''
        if self.table_ready and not self.variables["table_is_moving"]:
            # get me the current position
            old_pos = self.get_current_position()

            #Move the table down if necessary
            if move_down:
                error = self.move_down(lifting)
                if error != 0:
                    return error

            # Change the state of the table
            self.variables["table_is_moving"] = True
            pos_string = ""

            # Build the position to move to
            for i, pos in enumerate(position): # This is that the table is in the down position when moved
                if move_down and i==2 and not relative_move:
                    pos_string += str(float(pos)-float(lifting)) + " "
                else:
                    pos_string += str(pos) + " "

            # Move the table to the position
            if relative_move:
                move_command = self.__build_command(self.device["relative_move_to"], pos_string, self.device["command_order"])
            else:
                move_command = self.__build_command(self.device["move_to"], pos_string, self.device["command_order"])
            self.vcw.write(self.visa_resource, move_command[0], self.device.get("execution_terminator", ""))
            error = self.check_if_ready()
            if error != 0:
                return error

            # State that the table is not moving anymore
            self.variables["table_is_moving"] = False

            # Move the table back up again
            if move_down:
                error = self.move_up(lifting)
                if error != 0:
                    return error

            # Finally make sure the position is correct
            if relative_move:
                error = self.check_position([sum(x) for x in zip(old_pos, position)])
            else:
                error = self.check_position(position)
            if error != 0:
                return error

            self.variables["table_is_moving"] = False
            return 0

    def move_up(self, lifting):
        '''
        This function moves the table up

        :param lifting:  hight movement
        :return: none or errorcode
        '''
        if not self.variables["Table_state"]:
            errorcode = self.move_to([0,0,lifting], False, 0, True)
            if not errorcode:
                self.variables["Table_state"] = True
            return errorcode
        return 0

    def move_down(self, lifting):
        '''
        This function moves the table down

        :param lifting:  hight movement
        :return: none or errorcode
        '''
        if self.variables["Table_state"]:
            errorcode = self.move_to([0,0,-lifting], False, 0, True)
            if not errorcode:
                self.variables["Table_state"] = False
            return errorcode
        return 0

    @hf.raise_exception
    def set_joystick(self, bool):
        '''This enables or disables the joystick'''
        if self.table_ready:

            if bool:
                command = self.__build_command(self.device["set_joystick"], "1", self.device["command_order"])
            else:
                command = self.__build_command(self.device["set_joystick"], "0", self.device["command_order"])
            self.vcw.write(self.visa_resource, command[0], self.device.get("execution_terminator", ""))

    def set_joystick_speed(self, speed):
        '''This sets the speed for the joystick'''
        if self.table_ready:
            command = self.__build_command(self.device["set_joy_speed"], str(speed), self.device["command_order"])
            self.vcw.write(self.visa_resource, command[0], self.device.get("execution_terminator", ""))

    def set_axis(self, axis_list):
        '''This sets the axis on or off. axis_list must contain a list of type [x=bool, y=bool, z=bool]'''
        if self.table_ready:
            final_axis_list = []
            for i, axis in enumerate(axis_list):
                if axis:
                    final_axis_list.append("1 " + str(i+1))
                else:
                    final_axis_list.append("0 " + str(i+1))

            command = self.__build_command(self.device["set_axis"], final_axis_list, self.device["command_order"])
            for com in command:
                self.vcw.write(self.visa_resource, com, self.device.get("execution_terminator", ""))


    def stop_move(self):
        '''This function stops the table movement immediately'''
        if self.table_ready:
            command = self.__build_command(self.device["abort_movement"], "", self.device["command_order"])
            self.visa_resource.write(command)

class switching_control:
    """
    This class handles all switching controls of all switching matrices
    """

    def __init__(self, settings, devices, queue_to_main, shell):
        '''
        This class handles all switching actions

        :param settings: default settings ( state machine )
        :param devices: devices dict
        :param shell: UniDAQ shell object
        '''
        self.settings = settings
        self.message_to_main = queue_to_main
        self.devices = devices
        self.vcw = VisaConnectWizard.VisaConnectWizard()
        self.shell = None

    def reset_switching(self, device="all"):
        '''
        This function resets all switching or one device switching
        :param device: all oder device object:
        '''
        if device == "all": # opens all switches in all relays
            for dev in self.devices.values():
                if "Switching relay" in dev["Device_type"]:
                    self.change_switching(dev, []) # Opens all closed switches
        else:
            self.change_switching(device, [])

    def check_switching_action(self):
        """Checks what channels are closed on all switching devices"""
        for devices in self.devices.values():
            if "Switching relay" in devices["Device_type"] and "Visa_Resource" in devices:
                current_switching = str(self.vcw.query(devices["Visa_Resource"], devices["check_all_closed_channel"], devices.get("execution_terminator", ""))).strip()
                current_switching = self.pick_switch_response(devices, current_switching)
                self.settings["Defaults"]["current_switching"][devices["Display_name"]] = current_switching
                return current_switching

    def apply_specific_switching(self, switching_dict):
        """This function takes a dict of type {"Switching": [/switch nodes], ....} and switches to these specific type"""

        num_devices = len(switching_dict) # how many devices need to be switched
        devices_found = 0
        for devices in self.devices.values(): # Loop over all devices values (we need the display name)
            for display_names in switching_dict: # extract all devices names for identification
                if display_names in devices["Display_name"]:
                    switching_success = self.change_switching(devices, switching_dict[display_names])
                    devices_found += 1

        if num_devices != devices_found:
            l.error("At least one switching was not possible, no devices for switching included/connected")
            self.message_to_main.put({"MeasError": "At least one switching was not possible, no devices for switching included/connected"})
            switching_success = False

        return switching_success


    def switch_to_measurement(self, measurement):
        '''
        This function switches all switching systems to a specific measurement type

        :param measurement: string e.g. "IV", "CV" must be defined in the switching dict
        :return: true or false, so if switching was successfull or not
        '''

        # First find measurement
        switching_success = False
        if measurement in self.settings["Switching"]:
            # When measurement was found
            for name, switch_list in self.settings["Switching"][measurement].items():
                device_found = False
                for devices in self.devices.values():
                    if name in devices["Display_name"]:
                        device = devices
                        switching_success = self.change_switching(device, switch_list)
                        device_found = True
                if not device_found:
                    self.message_to_main.put({"RequestError": "Switching device: " + str(name) + " was not found in active resources. No switching done!"})
                    return False
            return switching_success
        else:
            l.error("Measurement " + str(measurement) + " switching could not be found in defined switching schemes.")
            self.message_to_main.put({"MeasError": "Measurement " + str(measurement) + " switching could not be found in defined switching schemes."})
            return False

    def __send_switching_command(self, device, order, list_of_commands, syntax):
        """Sends a switching command"""
        if list_of_commands:
            if list_of_commands[0]:
                mult_commands = ""
                for channel in list_of_commands:
                    mult_commands += channel + ","
                command = mult_commands[:-1]  # Get rid of last comma
                if len(syntax) > 1:
                    command = syntax[0] + command + syntax[1] # for the syntax
                command = self.build_command(device, (order, command))
                self.vcw.write(device["Visa_Resource"], command, device.get("execution_terminator", ""))  # Write new switching

    def pick_switch_response(self, device, current_switching):
        '''
        This function picks the string response and returns a list.
        :param current_switching: is a string containing the current switching

        '''
        syntax_list = device.get("switch_syntax", "")
        if syntax_list:
            syntax_list = syntax_list.split("channel")# gets me header an footer from syntax

        # Warning 7001 keithley sometimes seperates values by , and sometimes by : !!!!!!!!!
        # Sometimes it also happens that it mixes everything -> this means that the channel from to are closed etc.
        # Todo: implement the : exception

        if ":" in current_switching:
            l.error("The switching syntax for this is not yet implemented, discrepancies do occure from displayed to actually switched case. TODO")
            if "," in current_switching: # if this shitty mix happens
                current_switching = current_switching.replace(",", ":")
            if len(syntax_list) > 1:
                current_switching = current_switching[len(syntax_list[0]): -len(syntax_list[1])]
                return current_switching.strip().split(":")  # now we have the right commands
            else:
                return current_switching.strip().split(":")  # now we have the right commands

        if "," in current_switching:
            if ":" in current_switching: # if this shitty mix happens
                current_switching = current_switching.replace(":", ",")
            if len(syntax_list) > 1:
                current_switching = current_switching[len(syntax_list[0]): -len(syntax_list[1])]
                #current_switching = current_switching.split(syntax_list[0]).split(syntax_list[1])
                return current_switching.strip().split(",")  # now we have the right commands
            else:
                return current_switching.strip().split(",")  # now we have the right commands

        elif "@" in current_switching: # if no switching at all happens
            if len(syntax_list) > 1:
                current_switching = current_switching[len(syntax_list[0]): -len(syntax_list[1])]
                return current_switching.strip().split()  # now we have the right commands
            else:
                return current_switching.strip().split()  # now we have the right commands
        else:
            return current_switching.strip().split()  # now we have the right commands

    @hf.raise_exception
    @hf.run_with_lock
    def change_switching(self, device, config): # Has to be a string command or a list of commands containing strings!!
        '''
        Fancy name, but just sends the swithing command

        :param config: the list of nodes which need to be switched
        '''
        # TODO: check when switching was not possible that the programm shutsdown! Now the due to the brandbox this is switched off

        if type(config) == unicode or type(config) == str:
            configs = [config]
        else:
            configs = config

        if "Visa_Resource" in device: #Searches for the visa resource
            resource = device["Visa_Resource"]
        else:
            self.message_to_main.put({"RequestError": "The VISA resource for device " + str(device["Display_name"]) + " could not be found. No switching possible."})
            return -1

        current_switching = str(self.vcw.query(resource, device["check_all_closed_channel"], device.get("execution_terminator", ""))).strip()  # Get current switching
        syntax_list = device.get("switch_syntax", "")
        if syntax_list:
            syntax_list = syntax_list.split("channel")# gets me header an footer from syntax
        current_switching = self.pick_switch_response(device, current_switching)

        to_open_channels = list(set(current_switching) - (set(configs)))  # all channels which need to be closed
        to_close_channels = configs

        # Close channels
        self.__send_switching_command(device, device["set_close_channel"], to_close_channels, syntax_list)

        sleep(0.01) # Just for safety reasons because the brandbox is very slow

        # Open channels
        self.__send_switching_command(device, device["set_open_channel"], to_open_channels, syntax_list)

        # Check if switching is done (basically the same proceedure like before only in the end there is a check

        device_not_ready = True
        counter = 0
        while device_not_ready:
            current_switching = None
            all_done = str(self.vcw.query(resource, device["operation_complete"], device.get("execution_terminator", ""))).strip()
            if all_done == "1" or all_done == "Done":
                current_switching = str(self.vcw.query(resource, device["check_all_closed_channel"], device.get("execution_terminator", ""))).strip()
                syntax_list = device.get("switch_syntax", "")
                if syntax_list:
                    syntax_list = syntax_list.split("channel")  # gets me header an footer from syntax
                current_switching = self.pick_switch_response(device, current_switching)
                self.settings["Defaults"]["current_switching"][device["Display_name"]] = current_switching

                command_diff = list(set(configs).difference(set(current_switching)))
                if len(command_diff) != 0:  #Checks if all the right channels are closed
                    l.error("Switching to " + str(configs) + " was not possible. Difference read: " + str(current_switching))
                    print ("Switching to " + str(configs) + " was not possible. Difference read: " + str(current_switching))
                    device_not_ready = False
                    return False
                device_not_ready = False
                return True
            if counter > 5:
                device_not_ready = False
            counter += 1

        l.error("No response from switching system: " + device["Display_name"])
        self.message_to_main.put({"RequestError": "No response from switching system: " + device["Display_name"]})
        return False

    def build_command(self, device, command_tuple):
        """
        Builds the command correctly, so that device recognise the command

        :param device: device dictionary
        :param command_tuple: command, value
        """
        if type(command_tuple) == unicode:
            command_tuple = (str(command_tuple),) # so the correct casting is done

        for key, value in device.items():
            try:
                if command_tuple[0] == value: # finds the correct value
                    command_keyword = str(key.split("_")[-1])

                    if ("CSV_command_" + command_keyword) in device: # searches for CSV command in dict
                        data_struct = device["CSV_command_" + command_keyword].split(",")

                        final_string = str(command_tuple[0]) + " "  # so the key word

                        for i, given_orders in enumerate(command_tuple[1:]): # so if more values are given, these will be processed first
                            final_string += str(given_orders).upper() + ","  # so the value

                        if len(command_tuple[1:]) <= len(data_struct): # searches if additional data needs to be added
                            for data in data_struct[i+1:]:
                                # print device[command_keyword + "_" + data]
                                if command_keyword + "_" + data in device:
                                    final_string += str(device[command_keyword + "_" + data]).upper() + ","
                                else:
                                    final_string += ","# if no such value is in the dict

                        return final_string[:-1] # because there is a colon to much in it

                    else:
                        if len(command_tuple) > 1:
                            return str(command_tuple[0]) + " " + str(command_tuple[1])
                        else:
                            return str(command_tuple[0])

            except Exception as e:
                #print e
                pass

if __name__ == "__main__":


    trans = transformation()
    # Just for testing the transformation
    a1 = [350, 250, 12]
    a2 = [600, 250, 15]
    a3 = [350, 400, 12]

    b1 = [0, 0, 0]
    b2 = [250, 0, 0]
    b3 = [0, 150, 0]

    T, V0 = trans.transformation_matrix(b1,b2,b3,a1,a2,a3)
    print (T)
    print (V0)

    print (trans.vector_trans([12,23, 0], T,V0))