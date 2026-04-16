import math
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Airline Overbooking Simulator", layout="wide")

st.title("Airline Overbooking Simulator")
st.write(
    "Use simulation to estimate the best number of extra tickets to sell beyond seat capacity."
)

with st.sidebar:
    st.header("Inputs")
    seats = st.number_input("Plane capacity (seats)", min_value=1, value=100, step=1)
    ticket_price = st.number_input("Ticket price ($)", min_value=0.0, value=300.0, step=10.0)
    voucher_cost = st.number_input("Voucher cost per bumped passenger ($)", min_value=0.0, value=500.0, step=10.0)
    no_show_pct = st.slider("No-show probability (%)", min_value=0.0, max_value=100.0, value=10.0, step=0.5)
    max_overbook = st.number_input("Maximum overbooking to test", min_value=0, value=25, step=1)
    simulations = st.number_input("Simulation runs per option", min_value=100, value=20000, step=100)
    seed = st.number_input("Random seed", min_value=0, value=42, step=1)

st.markdown("---")

st.subheader("Problem setup")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Capacity", f"{seats}")
col2.metric("Ticket price", f"${ticket_price:,.0f}")
col3.metric("Voucher cost", f"${voucher_cost:,.0f}")
col4.metric("No-show rate", f"{no_show_pct:.1f}%")

p_show = 1 - no_show_pct / 100
rng = np.random.default_rng(seed)


def simulate_overbooking(capacity, overbook_by, price, voucher, show_prob, n_sims, random_gen):
    sold = capacity + overbook_by

    # Number of passengers who show up follows Binomial(sold, show_prob)
    showed_up = random_gen.binomial(sold, show_prob, size=n_sims)

    bumped = np.maximum(showed_up - capacity, 0)
    revenue = sold * price
    total_profit = revenue - bumped * voucher

    return {
        "Overbook by": overbook_by,
        "Tickets sold": sold,
        "Expected profit": float(np.mean(total_profit)),
        "Std profit": float(np.std(total_profit)),
        "Avg showed up": float(np.mean(showed_up)),
        "Prob over capacity": float(np.mean(showed_up > capacity)),
        "Avg bumped": float(np.mean(bumped)),
        "Max bumped": int(np.max(bumped)),
    }


results = []
for x in range(max_overbook + 1):
    # fresh RNG stream for reproducibility but still varying by x
    local_rng = np.random.default_rng(seed + x)
    results.append(
        simulate_overbooking(
            capacity=seats,
            overbook_by=x,
            price=ticket_price,
            voucher=voucher_cost,
            show_prob=p_show,
            n_sims=simulations,
            random_gen=local_rng,
        )
    )

results_df = pd.DataFrame(results)
best_row = results_df.loc[results_df["Expected profit"].idxmax()]

st.subheader("Recommended decision")
rec1, rec2, rec3 = st.columns(3)
rec1.metric("Best overbooking level", f"{int(best_row['Overbook by'])} seats")
rec2.metric("Expected profit", f"${best_row['Expected profit']:,.2f}")
rec3.metric("Chance of bumping passengers", f"{best_row['Prob over capacity']:.2%}")

st.write(
    f"Based on the simulation, the best choice is to overbook by **{int(best_row['Overbook by'])} seats**. "
    f"At that level, the model estimates an average profit of **${best_row['Expected profit']:,.2f}** per flight."
)

st.markdown("---")

st.subheader("Simulation results table")
formatted_df = results_df.copy()
formatted_df["Expected profit"] = formatted_df["Expected profit"].map(lambda x: f"${x:,.2f}")
formatted_df["Std profit"] = formatted_df["Std profit"].map(lambda x: f"${x:,.2f}")
formatted_df["Avg showed up"] = formatted_df["Avg showed up"].map(lambda x: f"{x:,.2f}")
formatted_df["Prob over capacity"] = formatted_df["Prob over capacity"].map(lambda x: f"{x:.2%}")
formatted_df["Avg bumped"] = formatted_df["Avg bumped"].map(lambda x: f"{x:,.2f}")
st.dataframe(formatted_df, use_container_width=True)

st.subheader("Expected profit by overbooking level")
st.line_chart(results_df.set_index("Overbook by")["Expected profit"])

st.subheader("Risk of bumping passengers")
st.line_chart(results_df.set_index("Overbook by")["Prob over capacity"])

with st.expander("See the model logic"):
    st.markdown(
        """
        **Simulation logic**

        - If capacity = 100 and overbook by = 5, then tickets sold = 105.
        - Each passenger has a probability of showing up equal to `1 - no_show_rate`.
        - The number of passengers who show up is simulated using a Binomial distribution.
        - If more passengers show up than available seats, the extra passengers are bumped.
        - Profit per flight is:

        `Profit = (tickets sold × ticket price) - (bumped passengers × voucher cost)`

        Since the problem states **no refund** for no-shows, all sold tickets still count as revenue.
        """
    )

st.subheader("Example from your class slide")
example_df = pd.DataFrame(
    {
        "Input": ["Seats", "Ticket price", "Voucher", "No-show %"],
        "Example value": [100, 300, 500, "10%"],
    }
)
st.table(example_df)