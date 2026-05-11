
from flask import Blueprint,jsonify,render_template,request
from .purge_engine import status,purge_legacy_db,build_view_model
real_data_purge_v90_bp=Blueprint('real_data_purge_v90',__name__)
@real_data_purge_v90_bp.route('/admin/real-data-purge')
def admin_real_data_purge(): return render_template('admin_real_data_purge_v90.html',status=status())
@real_data_purge_v90_bp.route('/api/v90/status')
def api_v90_status(): return jsonify(status())
@real_data_purge_v90_bp.route('/api/v90/purge',methods=['GET','POST'])
def api_v90_purge(): return jsonify(purge_legacy_db())
@real_data_purge_v90_bp.route('/real-feed')
def real_feed_page(): return render_template('v90_real_feed.html',vm=build_view_model('real-feed',request.args.get('force','false').lower()=='true'))
