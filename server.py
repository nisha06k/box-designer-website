import logging, logging.handlers, os, datetime, subprocess
from flask import Flask, render_template, request, redirect, send_from_directory

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BOX_TMP_DIR = os.path.join( BASE_DIR, 'tmp', 'boxes')

# setup logging
logging.basicConfig(level=logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler = logging.handlers.RotatingFileHandler(
    os.path.join(BASE_DIR,'boxmaker.log'), 'a', 10485760, 10) # 10MB
log_handler.setFormatter(log_formatter)
logger = logging.getLogger(__name__)
logger.propagate = False
logger.addHandler(log_handler)
logger.info("---------------------------------------------------------------------------")

@app.route("/", methods=['GET','POST'])
def index():
    if request.method == 'POST':
        validation_errors = _validate_box_params()
        if len(validation_errors)>0:
            error_str = ' '.join(validation_errors)
            logger.debug("Errors: "+error_str)
            return render_template('home.html', error=error_str)
        else:
            box_name = _box_name()
            logger.debug('Creating box '+box_name+"...")
            # convert it to millimeters
            measurements = ['width','height','depth','material_thickness','cut_width','notch_length']
            conversion = 1
            if request.form['units']=='in':
                conversion = 25.4
            elif request.form['units']=='cm':
                conversion = 10
            details = [str(float(request.form[m])*conversion) for m in measurements]
            # and add bounding box option
            if 'bounding_box' in request.form:
                details.append( 'true' )
            else:
                details.append( 'false' )
            # now render it
            logger.info( request.remote_addr + " - " + box_name + " - " + (" ".join(details)) )
            _render_box(box_name, details)
            return send_from_directory(BOX_TMP_DIR,box_name,as_attachment=True)
    else:
        return render_template("home.html")

def _render_box(file_name, params):
    boxmaker_jar_file = "BOX-v1.6.1.jar"
    pdf_file_path = os.path.join(BOX_TMP_DIR,file_name) 
    args = [ 'java', '-cp', boxmaker_jar_file, 'com.rahulbotics.boxmaker.CommandLine', pdf_file_path ] + params
    subprocess.call(args)

def _box_name():
    return 'box-'+datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")+'.pdf'

def _validate_box_params():
    errors = []
    errors+= _numeric_errors(request.form['width'],'Width')
    errors+= _numeric_errors(request.form['height'],'Height')
    errors+= _numeric_errors(request.form['depth'],'Depth')
    errors+= _numeric_errors(request.form['material_thickness'],'Material thickness')
    errors+= _numeric_errors(request.form['cut_width'],'Cut width')
    errors+= _numeric_errors(request.form['notch_length'],'Notch length')
    return errors

def _numeric_errors(str, name):
    try:
        float(str)
        return []
    except ValueError:
        return [ name + " must be a number!"]

if __name__ == "__main__":
    app.debug = False
    app.run()
