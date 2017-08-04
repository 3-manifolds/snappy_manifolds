f = open('census_knots.csv','r')
g = open('census_knots_fixed.csv','w')
for line in f:
    g.write(line.replace('[','"[').replace(']',']"'))
#    low = line.index('[')
#    high = line.index(']')
#    g.write(''.join( [line[:low].replace(',',';'), line[low:high].replace(" ",""), line[high:].replace(',',';')] ))
f.close()
g.close()
