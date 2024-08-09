import altair as alt


def hist(df, col, bins=20):
    assert col in df.columns, f"Column {col} not found"
    assert "origin" in df.columns, "Column 'origin' not found"

    return alt.Chart(df).mark_bar(color="red").encode(
        alt.X(col, bin=True),
        alt.Y('count()', stack=None),
        alt.Color('origin', scale=alt.Scale(
            domain=["all", "selected"],
            range=['ivory', 'lime']
        ))
    ).properties(height=200).configure_axisY(grid=False, labels=False)


def ts(df, x="datetime", y="median_lst"):
    return alt.Chart(df).mark_circle(size=300).encode(
        x=alt.X(f'{x}:T', title=''),
        y=alt.Y(f'{y}:Q', title='LST Median'),
        color=alt.Color('colors:N', scale=alt.Scale(
            domain=["Rejected", "Validated", "TBD"],
            range=['red', 'lime', 'orange']
            )
        )
        ).properties(
            height=300,
            width=600
        )