from distutils.core import setup

setup(
    name='ArduinoStepper',
    version='0.0.1',
    author='Floris van Breugel',
    author_email='floris@caltech.edu',
    packages = ['arduino_stepper'],
    license='BSD',
    description='python api for controlling a stepper motor via arduino',
    long_description=open('README.txt').read(),
)



