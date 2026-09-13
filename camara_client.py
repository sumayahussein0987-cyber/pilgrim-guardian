"""
Single import for all agents. Switches transparently between the mock
layer and the real Nokia sandbox based on CAMARA_MODE in .env.
"""
import config

if config.CAMARA_MODE == "live":
    import camara_client_live as _impl
else:
    import mocks.camara_mock as _impl

location_retrieval = _impl.location_retrieval
location_verification = _impl.location_verification
geofencing_subscribe = _impl.geofencing_subscribe
device_status = _impl.device_status
sim_swap_check = _impl.sim_swap_check
sim_swap_last_change = _impl.sim_swap_last_change
qod_create_session = _impl.qod_create_session
