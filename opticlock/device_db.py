# This is an example device database that needs to be adapted to your setup.
# The list of devices here is not exhaustive.

core_addr = "192.168.1.98"

device_db = {
    "core": {
        "type": "local",
        "module": "artiq.coredevice.core",
        "class": "Core",
        "arguments": {"host": core_addr, "ref_period":     0.8e-9}
    },
    "core_log": {
        "type": "controller",
        "host": "::1",
        "port": 1068,
        "command": "aqctl_corelog -p {port} --bind {bind} " + core_addr
    },
    "core_cache": {
        "type": "local",
        "module": "artiq.coredevice.cache",
        "class": "CoreCache"
    },
    "core_dma": {
        "type": "local",
        "module": "artiq.coredevice.dma",
        "class": "CoreDMA"
    },

    "i2c_switch0": {
        "type": "local",
        "module": "artiq.coredevice.i2c",
        "class": "PCA9548",
        "arguments": {"address": 0xe0}
    },
    "i2c_switch1": {
        "type": "local",
        "module": "artiq.coredevice.i2c",
        "class": "PCA9548",
        "arguments": {"address": 0xe2}
    },

    "ttl0": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLInOut",
        "arguments": {"channel": 0},
    },
    "ttl1": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLInOut",
        "arguments": {"channel": 1},
    },
    "ttl2": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLInOut",
        "arguments": {"channel": 2},
    },
    "ttl3": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLInOut",
        "arguments": {"channel": 3},
    },

    "ttl4": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLInOut",
        "arguments": {"channel": 4},
    },
    "ttl5": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLInOut",
        "arguments": {"channel": 5},
    },
    "ttl6": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLInOut",
        "arguments": {"channel": 6},
    },
    "ttl7": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLInOut",
        "arguments": {"channel": 7},
    },
    "ttl8": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 8},
    },
    "ttl9": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 9},
    },
    "ttl10": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 10},
    },
    "ttl11": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 11},
    },
    "ttl12": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 12},
    },
    "ttl13": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 13},
    },
    "ttl14": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 14},
    },
    "ttl15": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 15},
    },

    "spi_urukul0": {
        "type": "local",
        "module": "artiq.coredevice.spi2",
        "class": "SPIMaster",
        "arguments": {"channel": 16}
    },
    "ttl_urukul0_io_update": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 17}
    },
    "ttl_urukul0_sw0": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 18}
    },
    "ttl_urukul0_sw1": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 19}
    },
    "ttl_urukul0_sw2": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 20}
    },
    "ttl_urukul0_sw3": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 21}
    },
    "urukul0_cpld": {
        "type": "local",
        "module": "artiq.coredevice.urukul",
        "class": "CPLD",
        "arguments": {
            "spi_device": "spi_urukul0",
            "io_update_device": "ttl_urukul0_io_update",
            "refclk": 125e6,
            "clk_sel": 1
        }
    },
    "urukul0_ch0": {
        "type": "local",
        "module": "artiq.coredevice.ad9910",
        "class": "AD9910",
        "arguments": {
            "pll_n": 32,
            "chip_select": 4,
            "cpld_device": "urukul0_cpld",
            "sw_device": "ttl_urukul0_sw0"
        }
    },
    "urukul0_ch1": {
        "type": "local",
        "module": "artiq.coredevice.ad9910",
        "class": "AD9910",
        "arguments": {
            "pll_n": 32,
            "chip_select": 5,
            "cpld_device": "urukul0_cpld",
            "sw_device": "ttl_urukul0_sw1"
        }
    },
    "urukul0_ch2": {
        "type": "local",
        "module": "artiq.coredevice.ad9910",
        "class": "AD9910",
        "arguments": {
            "pll_n": 32,
            "chip_select": 6,
            "cpld_device": "urukul0_cpld",
            "sw_device": "ttl_urukul0_sw2"
        }
    },
    "urukul0_ch3": {
        "type": "local",
        "module": "artiq.coredevice.ad9910",
        "class": "AD9910",
        "arguments": {
            "pll_n": 32,
            "chip_select": 7,
            "cpld_device": "urukul0_cpld",
            "sw_device": "ttl_urukul0_sw3"
        }
    },

    "spi_urukul1": {
        "type": "local",
        "module": "artiq.coredevice.spi2",
        "class": "SPIMaster",
        "arguments": {"channel": 22}
    },
    "ttl_urukul1_sync": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLClockGen",
        "arguments": {"channel": 23, "acc_width": 4}
    },
    "ttl_urukul1_io_update": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 24}
    },
    "ttl_urukul1_sw0": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 25}
    },
    "ttl_urukul1_sw1": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 26}
    },
    "ttl_urukul1_sw2": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 27}
    },
    "ttl_urukul1_sw3": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 28}
    },
    "urukul1_cpld": {
        "type": "local",
        "module": "artiq.coredevice.urukul",
        "class": "CPLD",
        "arguments": {
            "spi_device": "spi_urukul1",
            "sync_device": "ttl_urukul1_sync",
            "io_update_device": "ttl_urukul1_io_update",
            "refclk": 125e6,
            "clk_sel": 1
        }
    },
    "urukul1_ch0": {
        "type": "local",
        "module": "artiq.coredevice.ad9910",
        "class": "AD9910",
        "arguments": {
            "pll_n": 32,
            "chip_select": 4,
            "cpld_device": "urukul1_cpld",
            "sw_device": "ttl_urukul1_sw0"
        }
    },
    "urukul1_ch1": {
        "type": "local",
        "module": "artiq.coredevice.ad9910",
        "class": "AD9910",
        "arguments": {
            "pll_n": 32,
            "chip_select": 5,
            "cpld_device": "urukul1_cpld",
            "sw_device": "ttl_urukul1_sw1"
        }
    },
    "urukul1_ch2": {
        "type": "local",
        "module": "artiq.coredevice.ad9910",
        "class": "AD9910",
        "arguments": {
            "pll_n": 32,
            "chip_select": 6,
            "cpld_device": "urukul1_cpld",
            "sw_device": "ttl_urukul1_sw2"
        }
    },
    "urukul1_ch3": {
        "type": "local",
        "module": "artiq.coredevice.ad9910",
        "class": "AD9910",
        "arguments": {
            "pll_n": 32,
            "chip_select": 7,
            "cpld_device": "urukul1_cpld",
            "sw_device": "ttl_urukul1_sw3"
        }
    },

    "spi_urukul2": {
        "type": "local",
        "module": "artiq.coredevice.spi2",
        "class": "SPIMaster",
        "arguments": {"channel": 29}
    },
    "ttl_urukul2_sync": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLClockGen",
        "arguments": {"channel": 30, "acc_width": 4}
    },
    "ttl_urukul2_io_update": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 31}
    },
    "ttl_urukul2_sw0": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 32}
    },
    "ttl_urukul2_sw1": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 33}
    },
    "ttl_urukul2_sw2": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 34}
    },
    "ttl_urukul2_sw3": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 35}
    },
    "urukul2_cpld": {
        "type": "local",
        "module": "artiq.coredevice.urukul",
        "class": "CPLD",
        "arguments": {
            "spi_device": "spi_urukul1",
            "sync_device": "ttl_urukul1_sync",
            "io_update_device": "ttl_urukul1_io_update",
            "refclk": 125e6,
            "clk_sel": 1
        }
    },
    "urukul2_ch0": {
        "type": "local",
        "module": "artiq.coredevice.ad9910",
        "class": "AD9910",
        "arguments": {
            "pll_n": 32,
            "chip_select": 4,
            "cpld_device": "urukul2_cpld",
            "sw_device": "ttl_urukul2_sw0"
        }
    },
    "urukul2_ch1": {
        "type": "local",
        "module": "artiq.coredevice.ad9910",
        "class": "AD9910",
        "arguments": {
            "pll_n": 32,
            "chip_select": 5,
            "cpld_device": "urukul2_cpld",
            "sw_device": "ttl_urukul2_sw1"
        }
    },
    "urukul2_ch2": {
        "type": "local",
        "module": "artiq.coredevice.ad9910",
        "class": "AD9910",
        "arguments": {
            "pll_n": 32,
            "chip_select": 6,
            "cpld_device": "urukul2_cpld",
            "sw_device": "ttl_urukul2_sw2"
        }
    },
    "urukul2_ch3": {
        "type": "local",
        "module": "artiq.coredevice.ad9910",
        "class": "AD9910",
        "arguments": {
            "pll_n": 32,
            "chip_select": 7,
            "cpld_device": "urukul2_cpld",
            "sw_device": "ttl_urukul2_sw3"
        }
    },

    "led0": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 36}
    },
    "led1": {
        "type": "local",
        "module": "artiq.coredevice.ttl",
        "class": "TTLOut",
        "arguments": {"channel": 37}
    }

}
