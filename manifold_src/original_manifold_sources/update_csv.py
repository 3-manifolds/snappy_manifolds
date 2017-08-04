tablename = 'nonorientable_cusped_census'
old = open(tablename+'.csv','r')
new_decs = open(tablename+'fixed.txt','r')
new = open(tablename+'updateddecorations.csv','w')

old_lines = old.readlines()
new.write(old_lines[0])

line_dict = {l.split(',')[0]:l for l in old_lines}
for line in new_decs:
    i, name, isosig = line.split(',')
    old_line = line_dict[i]
    split_line = old_line.split(',')
    split_line.pop()
    split_line.append(isosig)
    new.write(','.join(split_line))

