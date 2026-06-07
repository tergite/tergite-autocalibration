import dash
from dash import html

dash.register_page(__name__, title="Documentation")

layout = html.Div(
    [
        html.H1("Link to Documentation"),
        html.A(
            html.H1("Tergite Automatic Calibration"),
            href="https://tergite.github.io/tergite-autocalibration/",
        ),
    ]
)
