from wtforms import Form, SearchField, validators

class HCForm(Form):
    bowstyle  = SearchField('Bowstyle', list="bowstylelist", [validators.InputRequired("Please provide.")])
    roundname = SearchField('Round', [validators.InputRequired("Please provide.")]))
    gender    = SearchField('Gender under AGB')
    age       = SearchField('Age category')

