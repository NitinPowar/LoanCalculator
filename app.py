import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Set page layout to wide
st.set_page_config(page_title="Loan Part-Payment Calculator", layout="wide")
st.title("Personal Loan Part-Payment Calculator")

# -----------------------------------------------------------------------------
# TOP SECTION: INPUT FIELDS
# -----------------------------------------------------------------------------
st.subheader("1. Enter your Loan Details")
col1, col2, col3 = st.columns(3)

with col1:
    outstanding_principal = st.number_input("Total Outstanding Principal (₹)", min_value=1, value=500000, step=1000)
    current_emi = st.number_input("Current Monthly EMI (₹)", min_value=1, value=11122, step=100)

with col2:
    interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.1, max_value=100.0, value=12.0, step=0.1)
    current_tenure = st.number_input("Current Remaining Tenure (Months)", min_value=1, value=60, step=1)

with col3:
    part_payment = st.number_input("Part Payment Amount (₹)", min_value=0, value=100000, step=1000)
    reduction_target = st.radio("Prepayment Goal", ("Reduce Tenure (Keep EMI Same)", "Reduce EMI (Keep Tenure Same)"))

# -----------------------------------------------------------------------------
# CALCULATION ENGINE
# -----------------------------------------------------------------------------
monthly_rate = (interest_rate / 100) / 12

# Original Schedule Calculation (for interest comparison)
orig_balance = outstanding_principal
orig_total_interest = 0
for _ in range(int(current_tenure)):
    interest_this_month = orig_balance * monthly_rate
    principal_this_month = current_emi - interest_this_month
    if orig_balance <= 0:
        break
    if orig_balance < principal_this_month:
        orig_total_interest += interest_this_month
        break
    orig_total_interest += interest_this_month
    orig_balance -= principal_this_month

# Apply Part Payment immediately to the principal balance
new_balance = max(0, outstanding_principal - part_payment)

new_tenure = 0
new_emi = current_emi
new_total_interest = 0
emi_list = []

if new_balance > 0:
    if "Reduce Tenure" in reduction_target:
        # Scenario A: Keep EMI constant, calculate new shorter tenure
        temp_balance = new_balance
        while temp_balance > 0:
            interest_this_month = temp_balance * monthly_rate
            
            # Check if it's the last EMI (remaining balance + interest is less than usual EMI)
            if (temp_balance + interest_this_month) <= current_emi:
                last_emi = temp_balance + interest_this_month
                emi_list.append(round(last_emi))
                new_total_interest += interest_this_month
                temp_balance = 0
                new_tenure += 1
                break
            
            principal_this_month = current_emi - interest_this_month
            new_total_interest += interest_this_month
            temp_balance -= principal_this_month
            emi_list.append(round(current_emi))
            new_tenure += 1
            
            if new_tenure > 360:
                break
    else:
        # Scenario B: Keep Tenure constant, calculate lower EMI
        n = int(current_tenure)
        if (1 + monthly_rate)**n - 1 > 0:
            new_emi = new_balance * (monthly_rate * (1 + monthly_rate)**n) / ((1 + monthly_rate)**n - 1)
        else:
            new_emi = current_emi
            
        temp_balance = new_balance
        for i in range(n):
            interest_this_month = temp_balance * monthly_rate
            
            # Adjust the very last EMI to clear out rounding differences
            if i == n - 1:
                last_emi = temp_balance + interest_this_month
                emi_list.append(round(last_emi))
                new_total_interest += interest_this_month
                temp_balance = 0
                break
                
            principal_this_month = new_emi - interest_this_month
            new_total_interest += interest_this_month
            temp_balance -= principal_this_month
            emi_list.append(round(new_emi))
            
        new_tenure = current_tenure
        new_emi = emi_list if emi_list else new_emi

# Convert metric calculations to pure integers without decimal positions
orig_total_interest = int(round(orig_total_interest))
new_total_interest = int(round(new_total_interest))
interest_saved = max(0, int(round(orig_total_interest - new_total_interest)))
months_saved = max(0, int(current_tenure - new_tenure))

# -----------------------------------------------------------------------------
# BOTTOM SECTION: CHARTS AND VISUALISATIONS
# -----------------------------------------------------------------------------
st.write("---")
st.subheader("2. Comparison & Financial Impact")

# Metrics Summary Box (Integers only)
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Total Interest Saved", f"₹{interest_saved:,}")
with m2:
    if "Reduce Tenure" in reduction_target:
        st.metric("Tenure Reduction", f"{months_saved} Months Saved", f"New Tenure: {new_tenure} mos")
    else:
        avg_new_emi = int(round(np.mean(new_emi))) if isinstance(new_emi, list) else int(round(new_emi))
        st.metric("New Lower EMI", f"₹{avg_new_emi:,}", f"Dropped by: ₹{int(current_emi - avg_new_emi):,}")
with m3:
    if emi_list:
        st.metric("Final (Adjusted) EMI", f"₹{int(emi_list[-1]):,}", "Settled completely to ₹0")

# Create Columns for Side-by-Side Charts
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    # 1. Bar Chart: Tenure or EMI Comparison (Annotations Removed)
    fig_bar = go.Figure()
    
    if "Reduce Tenure" in reduction_target:
        y_vals = [current_tenure, new_tenure]
        text_vals = [f"{v}" for v in y_vals]
        
        fig_bar.add_trace(go.Bar(
            x=['Original Tenure', 'New Tenure'], 
            y=y_vals, 
            text=text_vals,
            textposition='outside', 
            marker_color=['#d3d3d3', '#00cc66']
        ))
        fig_bar.update_layout(
            title="Tenure Comparison (Months)", 
            yaxis_title="Months",
            yaxis=dict(tickformat="d")
        )
    else:
        avg_new_emi = int(round(np.mean(new_emi))) if isinstance(new_emi, list) else int(round(new_emi))
        y_vals = [current_emi, avg_new_emi]
        text_vals = [f"₹{v:,}" for v in y_vals]
        
        fig_bar.add_trace(go.Bar(
            x=['Original EMI', 'New EMI'], 
            y=y_vals, 
            text=text_vals,
            textposition='outside', 
            marker_color=['#d3d3d3', '#00cc66']
        ))
        fig_bar.update_layout(
            title="Monthly EMI Comparison (₹)", 
            yaxis_title="Amount in ₹",
            yaxis=dict(tickformat="d")
        )
        
    st.plotly_chart(fig_bar, use_container_width=True)

with chart_col2:
    # 2. Pie Chart: Interest Breakdown with Total Interest in the Center
    labels = ['Remaining Interest', 'Interest Saved']
    values = [new_total_interest, interest_saved]
    
    if interest_saved > 0:
        fig_pie = go.Figure(data=[go.Pie(
            labels=labels, 
            values=values, 
            hole=.5, # Created a slightly larger center hole for the text
            textinfo='value+percent', 
            texttemplate='%{value:,}<br>(%{percent})', 
            marker=dict(colors=['#ff4d4d', '#00cc66'])
        )])
        
        # ADDED: Total Interest value placed cleanly inside the center hole of the donut/pie chart
        fig_pie.update_layout(
            title="Interest Summary Structure",
            annotations=[dict(
                text=f"Original Total<br>Interest:<br><b>₹{orig_total_interest:,}</b>",
                x=0.5,
                y=0.5,
                font_size=13,
                font_family="Arial Black",
                showarrow=False
            )]
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Increase your part-payment to see interest savings graphs!")
