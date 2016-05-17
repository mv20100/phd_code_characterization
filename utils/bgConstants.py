import quantities as pq

name = "name"
symbol = "symbol"
beta = "beta"
delta = "delta"
gamma = "gamma"
T1CsD1 = "T1CsD1"
delta1CsD1 = "delta1CsD1"
gamma1CsD1 = "gamma1CsD1"
T1CsD2 = "T1CsD2"
delta1CsD2 = "delta1CsD2"
gamma1CsD2 = "gamma1CsD2"
atomicMass = "atomicMass"
sigma_bg = "sigma_bg"
D0 = "D0"

helium = {	name: "helium",
			symbol: "He",
			# HFS shift (Cs)
			beta: 1185 * pq.Hz / pq.torr,				#Beverini1981
			delta: 1.49 * pq.Hz / (pq.torr*pq.K),
			gamma: 0 * pq.Hz / (pq.torr * pq.K**2),
			# HFS shift (Cs)
			

			# Optical shift and broadening
			T1CsD1: 323 * pq.K,
			delta1CsD1: 4.24 * pq.MHz / pq.torr,		#Pitz2009
			gamma1CsD1: 24.13 * pq.MHz / pq.torr,
			T1CsD2: 313 * pq.K,
			delta1CsD2: 0.69 * pq.MHz / pq.torr,		#Pitz2010
			gamma1CsD2: 20.59 * pq.MHz / pq.torr,
			atomicMass: 6.64648e-24 * pq.g}

neon = {	name: "neon",
			symbol: "Ne",
			beta: 686 * pq.Hz / pq.torr,				#Kozlova2011
			delta: 0.266 * pq.Hz / (pq.torr*pq.K),
			gamma: -1.68e-3 * pq.Hz / (pq.torr * pq.K**2),
			T1CsD1: 313 * pq.K,
			delta1CsD1: -1.60 * pq.MHz / pq.torr,		#Pitz2009
			gamma1CsD1: 10.85 * pq.MHz / pq.torr,
			T1CsD2: 313 * pq.K,
			delta1CsD2: -2.58 * pq.MHz / pq.torr,		#Pitz2010
			gamma1CsD2: 9.81 * pq.MHz / pq.torr,
			atomicMass: 3.35082e-23 * pq.g,
			sigma_bg: 9.3e-23 * pq.cm**2,				#Kozlova2011
			D0: 0.153 * pq.cm**2 / pq.s}				#(For T0=0degC, P0=1atm)
		  
argon = {	name: "argon",
			symbol: "Ar",
			beta : -194.4 * pq.Hz / pq.torr,			#Kozlova2011
			delta: -1.138 * pq.Hz / (pq.torr*pq.K),
			gamma: 0 * pq.Hz / (pq.torr * pq.K**2),
			T1CsD1: 313 * pq.K,
			delta1CsD1: -6.47 * pq.MHz / pq.torr,		#Pitz2009
			gamma1CsD1: 18.31 * pq.MHz / pq.torr,
			T1CsD2: 313 * pq.K,
			delta1CsD2: -6.18 * pq.MHz / pq.torr,		#Pitz2010
			gamma1CsD2: 16.47 * pq.MHz / pq.torr,
			atomicMass: 6.6335e-23 * pq.g,
			sigma_bg: 104e-23 * pq.cm**2,				#Kozlova2011
			D0: 0.134 * pq.cm**2 / pq.s
			}				#(For T0=0degC, P0=1atm)

krypton = {	name: "krypton",
			symbol: "Kr",
			beta: -1450 * pq.Hz / pq.torr,			#Strumia1976
			delta: -1.9 * pq.Hz / (pq.torr*pq.K),
			gamma: 0 * pq.Hz / (pq.torr * pq.K**2),
			T1CsD1: 313 * pq.K,
			delta1CsD1: -5.46 * pq.MHz / pq.torr,		#Pitz2009
			gamma1CsD1: 17.82 * pq.MHz / pq.torr,
			T1CsD2: 313 * pq.K,
			delta1CsD2: -6.09 * pq.MHz / pq.torr,		#Pitz2010
			gamma1CsD2: 15.54 * pq.MHz / pq.torr,
			atomicMass: 1.3915e-22 * pq.g}

xenon = {	name: "xenon",
			symbol: "Xe",
			T1CsD1: 313 * pq.K,
			delta1CsD1: -6.43 * pq.MHz / pq.torr,		#Pitz2009
			gamma1CsD1: 19.74 * pq.MHz / pq.torr,
			T1CsD2: 313 * pq.K,
			delta1CsD2: -6.75 * pq.MHz / pq.torr,		#Pitz2010
			gamma1CsD2: 18.41 * pq.MHz / pq.torr,
			atomicMass: 2.18017e-22 * pq.g}
		  
hydrogen = {name: "hydrogen",
			symbol: "H_2",
			T1CsD1: 328 * pq.K,
			delta1CsD1: 1.11 * pq.MHz / pq.torr,		#Pitz2009
			gamma1CsD1: 20.81 * pq.MHz / pq.torr,
			T1CsD2: 313 * pq.K,
			delta1CsD2: -4.83 * pq.MHz / pq.torr,		#Pitz2010
			gamma1CsD2: 27.13 * pq.MHz / pq.torr}

nitrogen = {name: "nitrogen",
			symbol: "N_2",
			beta: 922.5 * pq.Hz / pq.torr,			#Kozlova2011
			delta: 0.824 * pq.Hz / (pq.torr*pq.K),
			gamma: -2.51e-3 * pq.Hz / (pq.torr * pq.K**2),
			T1CsD1: 318 * pq.K,
			delta1CsD1: -7.69 * pq.MHz / pq.torr,		#Pitz2009
			gamma1CsD1: 15.82 * pq.MHz / pq.torr,
			T1CsD2: 313 * pq.K,
			delta1CsD2: -6.2 * pq.MHz / pq.torr,		#Pitz2010
			gamma1CsD2: 19.18 * pq.MHz / pq.torr,
			atomicMass: 4.65173e-23 * pq.g,
			sigma_bg: 60e-23 * pq.cm**2,				#Kozlova2011
			D0: 0.087 * pq.cm**2 / pq.s}				#(For T0=0degC, P0=1atm)

methane = {	name: "methane",
			symbol: "CH_4",
			beta: -1050 * pq.Hz / pq.torr,			#Beverini1981
			delta: -1.47 * pq.Hz / (pq.torr*pq.K),
			gamma: 0 * pq.Hz / (pq.torr * pq.K**2),
			T1CsD1: 333 * pq.K,
			delta1CsD1: -9.28 * pq.MHz / pq.torr,		#Pitz2009
			gamma1CsD1: 29.00 * pq.MHz / pq.torr,
			T1CsD2: 313 * pq.K,
			delta1CsD2: -8.86 * pq.MHz / pq.torr,		#Pitz2010
			gamma1CsD2: 25.84 * pq.MHz / pq.torr}

ethane = 	{name: "ethane",
			symbol: "C_{2}H_{6}",
			beta: -1852 * pq.Hz / pq.torr,			#Beverini1981
			delta: -1.87 * pq.Hz / (pq.torr*pq.K),
			gamma: 0 * pq.Hz / (pq.torr * pq.K**2),
			T1CsD1: 331 * pq.K,
			delta1CsD1: -8.54 * pq.MHz / pq.torr,		#Pitz2009
			gamma1CsD1: 26.70 * pq.MHz / pq.torr,
			T1CsD2: 313 * pq.K,
			delta1CsD2: -9.38 * pq.MHz / pq.torr,		#Pitz2010
			gamma1CsD2: 26.14 * pq.MHz / pq.torr}