test:
	nosetests --verbosity=2 --detailed-errors -x

pdb:
	nosetests --verbosity=2 --detailed-errors -x --pdb --nocapture
