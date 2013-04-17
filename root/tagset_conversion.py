'''
Created on Feb 24, 2012

@author: 100457636
'''
from string import lower


class TagsetConverter(): 

    def __init__(self):
        self._claws_brown_map = { 
                    'APPGE': 'PP$$',
                    'AT' : 'AT',
                    'AT1' : 'AT',
                    # 'BCL' : '',
                    'CC' : 'CC',
                    'CCB' : 'CC',
                    'CS' : 'CS',
                    'CSA' : 'CS',
                    'CSN' : 'CS',
                    'CST' : 'CS',
                    'CSW' : 'CS',
                    'DA': 'AP' ,
                    'DA1' : 'AP',
                    'DA2' : 'AP',
                    'DAR' : 'AP',
                    'DAT' : 'AP',
                    'DB' : 'ABN',
                    'DB2' : 'ABX',
                    'DD' : 'DTI',
                    'DT1' : 'DT',
                    'DD2' : 'DTS',
                    'DDQ' : 'WDT',
                    'DDQGE' : 'WP$',
                    'DDQV' : 'WDT',
                    'EX' : 'EX',
                    #'FO' : '',
                    #'FU' : '',
                    'FW' : 'FW', # abusing the Brown notation
                    #'GE' : '',
                    'IF' : 'IN',
                    'II' : 'IN',
                    'IO' : 'IN',
                    'IW' : 'IN',
                    'JJ' : 'JJ',
                    'JJR' : 'JJR',
                    'JJT' : 'JJT',
                    'JK' : 'JJ',
                    'MC' : 'CD',
                    'MC1' : 'CD',
                    'MC2' : 'CD',
                    'MCGE' : 'CD$',
                    'MCMC' : 'CD',
                    'MD' : 'OD',
                    'MF' : 'CD',
                    'ND1' : 'NR',
                    'NN' : 'NN',
                    'NN1' : 'NN',
                    'NN2' : 'NNS',
                    'NNA' : 'NN',
                    'NNB' : 'NN',
                    'NNL1' : 'NN',
                    'NNL2' : 'NNS',
                    'NNO' : 'NN',
                    'NNO2' : 'NNS',
                    'NNT1' : 'NN',
                    'NNT2' : 'NNS',
                    'NNU' : 'NN',
                    'NNU1' : 'NN',
                    'NNU2' : 'NNS',
                    'NP' : 'NP',
                    'NP1' : 'NP',
                    'NP2' : 'NPS',
                    'NPD1' : 'NR',
                    'NPD2' : 'NRS',
                    'NPM1' : 'NP',
                    'NPM2' : 'NPS',
                    'PN' : 'PN',
                    'PN1' : 'PN',
                    'PNQO' : 'WPO',
                    'PNQS' : 'WPO',
                    'PNQV' : 'WPS',
                    'PNX1' : 'PPL',
                    'PPGE' : 'PP$$',
                    'PPH1' : 'PPS',
                    'PPHO1' : 'PPO',
                    'PPHO2' : 'PPO',
                    'PPHS1' : 'PPS',
                    'PPHS2' : 'PPSS',
                    'PPIO1' : 'PPO',
                    'PPIO2' : 'PPO',
                    'PPIS1' : 'PPSS',
                    'PPIS2' : 'PPSS',
                    'PPX1' : 'PPL',
                    'PPX2' : 'PPLS',
                    'PPY' : 'PPO',
                    'RA' : 'RB',
                    'REX' : 'RB',
                    'RG' : 'QL',
                    'RGQ' : 'QL',
                    'RGR' : 'RBR',
                    'RGT' : 'RBT',
                    'RL' : 'RB',
                    'RP' : 'RP',
                    'RPK' : 'RP',
                    'RR' : 'RB',
                    'RRQ' : 'WRB',
                    'RRQV' : 'WRB',
                    'RRR' : 'RBR',
                    'RRT' : 'RBT',
                    'RT' : 'NR',
                    'TO' : 'TO',
                    'UH' : 'UH',
                    'VB0' : 'BE',
                    'VBDR' : 'BED',
                    'VBDZ' : 'BEDZ',
                    'VBG' : 'BEG',
                    'VBI' : 'BE',
                    'VBM' : 'BEM',
                    'VBN' : 'BEN',
                    'VBR' : 'BER',
                    'VBZ' : 'BEZ',
                    'VD0' : 'DO',
                    'VDD' : 'DOD',
                    'VDG' : 'VBG',
                    'VDI' : 'DO',
                    'VDN' : 'DOD',
                    'VDZ' : 'DOZ',
                    'VH0' : 'HV',
                    'VHD' : 'HVD',
                    'VHG' : 'HVG',
                    'VHI' : 'HV',
                    'VHN' : 'HVN',
                    'VHZ' : 'HVZ',
                    'VM'  : 'MD',
                    'VMK' : 'MD',
                    'VV0' : 'VB',
                    'VVD' : 'VBD',
                    'VVG' : 'VBG',
                    'VVGK' : 'VBG',
                    'VVI' : 'VB',
                    'VVN' : 'VBN',
                    'VVNK' : 'VBN',
                    'VVZ' : 'VBZ',
                    'XX' : '*'
                    #'ZZ1' : '',
                    #'ZZ2' : ''
                 }
        
    def claws7ToBrown (self, tag):
        t = tag.upper()
        return self._claws_brown_map[t] if t in self._claws_brown_map else None
    
    def brownToWordNet(self, tag):
        tag = tag.lower()
        l = tag[0]  # first letter
        ll = tag[:2]  # two first letters
        if ll == 'np':
            return None
        elif l == 'n':
            return 'n'
        elif l in ('b', 'v', 'h') or ll == 'do':
            return 'v'
        elif l in ('r') or ll == 'wr':
            return 'r'
        elif l == 'j':
            return 'a'
        else:
            return None