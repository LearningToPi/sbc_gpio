''' 
General GPIO configuration constants and set function using general linux kernel configuration:
https://www.kernel.org/doc/Documentation/devicetree/bindings/gpio/gpio.txt

Override on a per device basis as needed.
'''

ACTIVE_HIGH =     0b0 # bit 0
ACTIVE_LOW =      0b1 # bit 0
PUSH_PULL =       0b0 # bit 1
SINGLE_ENDED =    0b1 # bit 1
OPEN_SOURCE =     0b0 # bit 2
OPEN_DRAIN =      0b1 # bit 2
SLEEP_MAINTAIN =  0b0 # bit 3
SLEEP_STATE_LOST= 0b1 # bit 3
PULL_UP =         0b01 # bits 4 and 5
PULL_DOWN =       0b10 # bits 4 and 5
PULL_NONE =       0b00 # bits 4 and 5


FLAGS = {
    'ACTIVE_HIGH':       {'value': 0b0, 'offset': 0}, 
    'ACTIVE_LOW':        {'value': 0b1, 'offset': 0}, 
    'PUSH_PULL':         {'value': 0b0, 'offset': 1}, 
    'SINGLE_ENDED':      {'value': 0b1, 'offset': 1}, 
    'OPEN_SOURCE':       {'value': 0b0, 'offset': 2},
     'OPEN_DRAIN':       {'value': 0b1, 'offset': 2}, 
     'SLEEP_MAINTAIN':   {'value': 0b0, 'offset': 3}, 
     'SLEEP_STATE_LOST': {'value': 0b1, 'offset': 3}, 
     'PULL_UP':          {'value': 0b01, 'offset': 4}, 
     'PULL_DOWN':        {'value': 0b10, 'offset': 4}, 
     'PULL_NONE':        {'value': 0b00, 'offset': 4}
     }

def set_gpio_flags(*args) -> int:
    ''' Return an integer based on the flags sent.'''
    ret_value = 0
    for arg in args:
        if arg.upper() not in FLAGS.keys():
            raise ValueError(f'Value {arg} not in list of supported flags: {FLAGS}')
        ret_value = ret_value | (FLAGS[arg.upper()].get('value', 0b0) << FLAGS[arg.upper()].get('offset', 0))
    return ret_value