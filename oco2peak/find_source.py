# AUTOGENERATED! DO NOT EDIT! File to edit: notebooks/oco2peak_find_source.ipynb (unless otherwise specified).

__all__ = ['estimate_emission', 'plot_emission']

# Cell
import numpy as np
from oco2peak import find_peak

# Cell
from sklearn.linear_model import LinearRegression

def estimate_emission(df_peak, peak_param):

    X=df_peak.latitude.to_numpy()
    Y=df_peak.longitude.to_numpy()

    model = LinearRegression()
    model.fit(X.reshape(-1, 1), Y)
    slope = model.coef_[0]
    intercept = model.intercept_

    # Total Column Water Vapour
    tcwv = peak_param['tcwv']
    psurf = peak_param['surface_pressure']
    u10 = peak_param['windspeed_u']
    v10 = peak_param['windspeed_v']

    u_track = slope
    b_track = intercept
    v_track = 1.
    vec_track = np.array([u_track, v_track])
    vec_track = vec_track / np.sqrt(vec_track.dot(vec_track))   # unit  vector
    vec_wind = np.array([u10,v10])
    # unit vector orthogonal to the OCO-2 track
    vec_trackorth = np.array([vec_track[1],-1*vec_track[0]])
    # project wind vector on it
    wind_angle = np.angle(v10+1j*u10, deg = True)  # clockwise angle from the North, of the wind direction
    wind_proj = abs(np.dot(vec_wind,vec_trackorth))
    rg = 9.80665     # m s-2
    density = abs(peak_param['amplitude']*1e-3) * 0.04401 / 0.02896 *(psurf/rg - tcwv)  # ppm km => kg/m
    gCO2_per_s = density*1000.*wind_proj   # gCO2/s
    ktCO2_per_h = gCO2_per_s/1e9*3600.   # ktCO2/h
    emission = {
        'sat_track_u' : u_track,
        'sat_track_b' : b_track,
        'sat_track_v' : v_track,
        'wind_u' : u10,
        'wind_v' : v10,
        'gCO2_per_s' : gCO2_per_s,
        'ktCO2_per_h' : ktCO2_per_h
    }
    return emission


# Cell
import plotly.graph_objects as go

def plot_emission(df_peak, peak_param, emission):
    fig = go.Figure()
    _ = fig.add_trace(go.Scatter(x=df_peak.latitude, y=df_peak.longitude, marker_color=df_peak.xco2, mode='markers', name='xco2'))
    x_point = np.linspace(df_peak.latitude.min(), df_peak.latitude.max(), 200, endpoint=False)
    y_plot = x_point * emission['sat_track_u'] + emission['sat_track_b']
    _ = fig.add_trace(go.Scatter(x=x_point, y=y_plot, mode='markers', name='Satellite track')) # OLS = Ordinary Least Squares
    wind_u = emission['wind_u']
    wind_v = emission['wind_v']
    _ = fig.add_shape(
        # Wind vector
        type="line",
        x0=peak_param['latitude'],
        y0=peak_param['longitude'],
        x1=peak_param['latitude']+wind_u*0.3,
        y1=peak_param['longitude']+wind_v*0.3,
        name='Wind',
        line=dict(color="MediumPurple",width=4,dash="dot")
    )

    _ = fig.update_layout(
        showlegend=False,
        annotations=[
            dict(
                x=peak_param['latitude'],
                y=peak_param['longitude'],
                xref='x',
                yref='y',
                text="Wind",
                showarrow=True,
                arrowhead=1,
                ax=peak_param['latitude']+wind_u*0.3,
                ay=peak_param['longitude']+wind_v*0.3,
            )
        ]
    )
    return fig