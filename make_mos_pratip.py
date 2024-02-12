
# ======================================================================= #
def make_mos_from_Molden(moldenfile, QMin):
    '''
    This function collects mo-coefficients from molden and returns them in correct order of orbitals 
    with respect to the original order of pySCF in Columbus format.
    
    Upto p functions, the orders are same. 

    Spherical:
    PySCF Order: d: (-2, -1, 0, 1, 2), f: (-3, -2, -1, 0, 1, 2, 3), g: (0, +1, -1, +2, -2, +3, -3, +4, -4) 
    Molden Order: d: (0, +1, -1, +2, -2), f: (0, +1, -1, +2, -2, +3, -3), g: (0, +1, -1, +2, -2, +3, -3, +4, -4)

    Cartesian:
    PySCF Order: d: (xx, xy, xz, yy, yz), f: (xxx, xxy, xxz, xyy, xyz, xzz, yyy, yyz, yzz, zzz), 
                 g: (xxxx, xxxy, xxxz, xxyy, xxyz, xxzz, xyyy, xyyz, xyzz, xzzz, yyyy, yyyz, yyzz, yzzz, zzzz)
    Molden Order: d: (xx, yy, zz, xy, xz, yz), f: (xxx, yyy, zzz, xyy, xxy, xxz, xzz, yzz, yyz, xyz), 
                 g: (xxxx, yyyy, zzzz, xxxy, xxxz, yyyx, yyyz, zzzx, zzzy, xxyy, xxzz, yyzz, xxyz, yyxz, zzxy)

    '''
    # read file
    data = readfile(moldenfile)

    # basis info
    shells = {'s': (1, 1), 'p': (3, 3), 'd': (6, 5), 'f': (10, 7), 'g': (15, 9)}
    mode = {'s': 0, 'p': 0, 'd': 0, 'f': 0, 'g': 0}    # 0: cartesian, 1: spherical
    for line in data:
        if '[5d' in line.lower():
            mode['d'] = 1
        if '7f]' in line.lower():
            mode['f'] = 1
        if '[9g]' in line.lower():
            mode['g'] = 1
    NAOs = [0, 0]          # 0: with full cart basis, 1: as in Molden
    aos = []

    #Pratip: Introducing dictionary for reordering basis function index to the order of pyscf
    basis_order = {'spherical':{'s': (0,), 'p': (0,1,2), 'd': (4,2,0,1,3), 'f': (6,4,2,0,1,3,5), 'g': (8,6,4,2,0,1,3,5,7)},
               'cartesian': {'s': (0,), 'p': (0,1,2), 'd': (0,3,5,1,2,4), 'f': (0,6,9,3,1,2,5,8,7,4), 'g': (0,10,14,1,2,6,11,9,13,3,5,12,4,7,8)}}    

    #Pratip: check what type of basis set
    GTO_TYPE = 'cartesian'
    for line in data:
        if '[5d' in line.lower():
            GTO_TYPE = 'spherical'

    # get basis info
    for iline, line in enumerate(data):
        if '[gto]' in line.lower():
            break
    else:
        print('Could not find basis set in %s!' % (moldenfile))
        sys.exit(60)
    while True:
        iline += 1
        if iline >= len(data):
            print('Could not find basis set in %s!' % (moldenfile))
            sys.exit(61)
        line = data[iline].lower()
        if '[' in line:
            break
        s = line.split()
        if len(s) >= 1 and s[0] in shells:
            NAOs[0] += shells[s[0]][0]
            NAOs[1] += shells[s[0]][mode[s[0]]]
            aos.append(s[0])


    for iline, line in enumerate(data):
        if '[mo]' in line.lower():
            break
    else:
        print('Could not find MO coefficients in %s!' % (moldenfile))
        sys.exit(62)

    #Pratip: Introducing generalization between cartesian and spherical basis
    NAO = NAOs[0] # default cartesian
    if GTO_TYPE == 'spherical':
        NAO = NAOs[1]

    #NAO = NAOs[1]
    # get coefficients for alpha
    NMO_A = NAO
    MO_A = [[0. for i in range(NAO)] for j in range(NMO_A)]
    for imo in range(NMO_A):
        for iao in range(NAO):
            jline = iline + 4 + iao + (NAO + 3) * imo
            line = data[jline]
            MO_A[imo][iao] = float(line.split()[1])
    
    # Pratip: This bit reorders the mo-coefficients collected from molden file 
    MO_B = []
    #Generalized for all angular momentums
    for mo in MO_A:

        mo_reordered = []
        count = 0
        for ao_type in aos:
            
            for i in basis_order[GTO_TYPE][ao_type]:
                mo_reordered.append(mo[count+i])
                                
            count += len(basis_order[GTO_TYPE][ao_type])

        MO_B.append(mo_reordered)

    # handle frozen core
    # print QMin['frozcore']
    NMO = NMO_A - QMin['frozcore']

    string = '''2mocoef
header
 1
MO-coefficients from Gaussian
 1
 %i   %i
 a
mocoef
(*)
''' % (NAO, NMO)
    x = 0
    for imo, mo in enumerate(MO_B):     # Pratip: With the new reordered MOs
        if imo < QMin['frozcore']:
            continue
        for c in mo:
            if x >= 3:
                string += '\n'
                x = 0
            string += '% 6.12e ' % c
            x += 1
        if x > 0:
            string += '\n'
            x = 0
    string += 'orbocc\n(*)\n'
    x = 0
    for i in range(NMO):
        if x >= 3:
            string += '\n'
            x = 0
        string += '% 6.12e ' % (0.0)
        x += 1

    return string

# ======================================================================= #
