import streamlit as st

from mlox.configs import LiteLLM, get_servers, update_service
from mlox.remote import fs_read_file


st.set_page_config(page_title="LiteLLM Install Page", page_icon="🌍")
st.markdown("# LiteLLM Install")

servers = get_servers()
target_ip = st.selectbox("Choose Server", list(servers.keys()))
server = servers[target_ip]

target_path = st.text_input("Install Path", f"/home/{server.user}/my_litellm")
port = st.text_input("Port", "4000")
ui_user = st.text_input("Username", "admin")
ui_pw = st.text_input("Password", "admin0123")
master_key = st.text_input("Master key", "sk-1234")
slack = st.text_input("Slack Webhook", "")

service = LiteLLM(server, target_path, ui_user, ui_pw, port, slack, master_key)
update_service(service)
c1, c2, c3, c4 = st.columns([15, 15, 15, 55])
if c1.button("Setup"):
    service.setup()
if c2.button("Start"):
    service.spin_up()
if c3.button("Stop"):
    service.spin_down()

with st.expander("Details"):
    st.write(service)


files = [
    "litellm-config.yaml",
    "service.env",
    "docker-compose.yaml",
    "cert.pem",
]
tabs = st.tabs(files)
for i in range(len(files)):
    with tabs[i]:
        with service.server as conn:
            res = fs_read_file(
                conn,
                f"{service.target_path}/{files[i]}",
                format="yaml" if files[i][-4:] == "yaml" else None,
            )
            if isinstance(res, str):
                st.text(res)
            else:
                st.write(res, unsafe_allow_html=True)
            print(res)

st.sidebar.header("Links")
st.sidebar.page_link(service.get_service_url(), label="LiteLLM")
