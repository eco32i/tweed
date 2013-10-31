import operator

def parse_header(header):
    '''
    Parses the fasta record header, one of two forms:
        >NODE_45_length_92_cov_13.978261
    or
        >Locus_1_Transcript_5/59_Confidence_0.009_Length_195
    and return dict suitable for constructing either Contig or
    Transcript instances.
    '''
    bits = header.strip('>').lower().split('_')
    d = {}
    for i, bit in enumerate(bits):
        value = ''
        if i % 2 == 0:
            if bit in ('node', 'transcript'):
                key = '{field}_id'.format(field=bit)
            elif bit == 'cov':
                key = 'coverage'
            else:
                key = bit
            try:
                value = bits[i+1].split('/')[0]
            except IndexError:
                pass
            d.update({key: value,})
    return d
    
def get_contig_ids(transcript):
    '''
    Takes a string representing a transcript from contig-ordering.txt
    in a 
        -1:123-(0)->6219:124-(0)->6220:130-(0)->6221:138-(0)
    format and returns a list of contig ids to be used in database
    query to compute transcript coverage.
    '''
    bits = transcript.tostring().split('->')
    ctg_ids = [abs(int(ctg.split(':')[0])) for ctg in bits]
    return ctg_ids


def get_next_hit(handle):
    '''
    Takes an open blastresults.txt file and returns hits per
    transcripts.
    '''
    is_header = False
    query = hits = None
    while True:
        line = handle.readline().strip()
        if line.startswith('#'):
            if is_header:
                if line.endswith('hits found'):
                    hits = int(line.split()[1])
                    is_header = False
                    break;
                elif line.startswith('# Query:'):
                    query = line.split()[-1]
            elif line.startswith('# BLASTN'):
                is_header = True
        elif not line:
            break
    return query, hits
