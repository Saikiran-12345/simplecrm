from flask import render_template, current_app
from app.analytics import bp
from app.auth.utils import login_required
from app.utils.storage import BaseStorage
from collections import defaultdict
import datetime

def get_storage(name):
    return BaseStorage(current_app.config['DATA_DIR'], name)

@bp.route('/analytics')
@login_required
def index():
    # 1. Lead Conversion Rate
    leads = get_storage('leads').get_all_records()
    total_leads = len(leads)
    converted_leads = len([l for l in leads if l.get('status') == 'Converted'])
    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0.0
    
    # 2. Opportunity Win/Loss Ratio
    opps = get_storage('opportunities').get_all_records()
    won_opps = len([o for o in opps if o.get('stage') == 'Won'])
    lost_opps = len([o for o in opps if o.get('stage') == 'Lost'])
    resolved_opps = won_opps + lost_opps
    win_rate = (won_opps / resolved_opps * 100) if resolved_opps > 0 else 0.0
    
    # 3. Sales by Month
    sales = get_storage('sales').get_all_records()
    sales_by_month = defaultdict(float)
    for s in sales:
        date_str = s.get('sales_date', '')
        if len(date_str) >= 7:
            month = date_str[:7] # YYYY-MM
            sales_by_month[month] += float(s.get('total', 0))
            
    # Sort months chronologically
    sorted_months = sorted(sales_by_month.keys())
    monthly_sales = [{'month': m, 'total': sales_by_month[m]} for m in sorted_months][-6:] # Last 6 months
    
    # Find max for bar chart scaling
    max_sales = max([m['total'] for m in monthly_sales]) if monthly_sales else 1.0
    if max_sales == 0: max_sales = 1.0
    
    return render_template('analytics/index.html', 
                           conversion_rate=conversion_rate, 
                           total_leads=total_leads,
                           win_rate=win_rate,
                           won_opps=won_opps,
                           lost_opps=lost_opps,
                           monthly_sales=monthly_sales,
                           max_sales=max_sales)
