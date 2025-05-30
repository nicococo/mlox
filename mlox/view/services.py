import pandas as pd
import streamlit as st

from typing import cast

from mlox.infra import Infrastructure
from mlox.config import load_all_service_configs


def installed_services():
    st.markdown("""
    # Services
    This is where you can manage your services.""")
    infra = cast(Infrastructure, st.session_state.mlox.infra)

    st.markdown("### Service List")

    services = []
    for bundle in infra.bundles:
        for stateful_service in bundle.services:
            services.append(
                {
                    "ip": bundle.server.ip,
                    "name": stateful_service.service.name,
                    "version": stateful_service.config.version,
                    "link": stateful_service.service.service_url,
                    "state": stateful_service.state,
                    # "tags": bundle.tags,
                    # "services": [s.name for s in bundle.services],
                    # "specs": f"{info['cpu_count']} CPUs, {info['ram_gb']} GB RAM, {info['storage_gb']} GB Storage, {info['pretty_name']}",
                }
            )

    df = pd.DataFrame(services, columns=["ip", "name", "version", "state", "link"])
    select_server = st.dataframe(
        df,
        use_container_width=True,
        selection_mode="single-row",
        hide_index=True,
        on_select="rerun",
        key="service-select",
    )

    if len(select_server["selection"].get("rows", [])) == 1:
        idx = select_server["selection"]["rows"][0]
        ip = services[idx]["ip"]
        service_name = services[idx]["name"]

        c1, c2, _, c3 = st.columns([20, 20, 40, 20])
        if c1.button("Setup"):
            with st.spinner(f"Setting up service {service_name}...", show_time=True):
                infra.setup_service(ip, service_name, state="setup")
            st.rerun()

        if c2.button("Teardown"):
            with st.spinner(f"Deleting service {service_name}...", show_time=True):
                infra.setup_service(ip, service_name, state="teardown")
            st.rerun()

        bundle, stateful_service = infra.get_stateful_service(ip, service_name)
        if "settings" in stateful_service.config.ui:
            settings_func = stateful_service.config.ui["settings"]

            import importlib

            try:
                # Split the string into module path and function name
                module_path, func_name = settings_func.rsplit(".", 1)
                # Import the module
                module = importlib.import_module(module_path)
                # Get the function object
                callable_settings_func = getattr(module, func_name)

                # Call the function with the required arguments
                callable_settings_func(infra, bundle, stateful_service.service)

            except (ImportError, AttributeError) as e:
                st.error(f"Could not load settings UI for this service: {e}")
            except Exception as e:
                st.error(f"An error occurred while rendering settings UI: {e}")


def available_services():
    st.markdown("""
    ### Services
    This is where you can manage your services.""")
    infra = cast(Infrastructure, st.session_state.mlox.infra)

    # with st.expander("Add Server"):
    configs = load_all_service_configs("./stacks")

    services = []
    for service in configs:
        services.append(
            {
                "name": service.name,
                "version": service.version,
                "maintainer": service.maintainer,
                "description": service.description,
                "description_short": service.description_short,
                "links": [f"{k}: {v}" for k, v in service.links.items()],
                "requirements": [f"{k}: {v}" for k, v in service.requirements.items()],
                "ui": [f"{k}" for k, v in service.ui.items()],
                "backend": [f"{k}" for k, v in service.build.items()],
            }
        )

    c1, _, _ = st.columns(3)
    search_filter = c1.text_input(
        "Search",
        value="",
        key="search_filter",
        label_visibility="collapsed",
        placeholder="Search for services...",
    )
    if len(search_filter) > 0:
        services = [s for s in services if search_filter.lower() in s["name"].lower()]

    df = pd.DataFrame(services)
    select = st.dataframe(
        df[
            [
                "name",
                "version",
                # "maintainer",
                # "description",
                # "links",
                # "requirements",
                "backend",
                "description_short",
            ]
        ],
        use_container_width=True,
        selection_mode="single-row",
        hide_index=True,
        on_select="rerun",
        key="avail-service-select",
    )

    if len(select["selection"].get("rows", [])) == 1:
        selected = select["selection"]["rows"][0]
        config = configs[selected]
        c2, c3, c4, _ = st.columns([25, 25, 15, 35])
        select_backend = c2.selectbox(
            "Backend",
            list(config.build),
            format_func=lambda x: f"{x} Backend",
            key="select_backedn",
        )
        bundle = c3.selectbox(
            "Server",
            infra.list_bundles_with_backend(backend=select_backend),
            format_func=lambda x: f"{x.name} {x.server.ip}",
        )
        if c4.button("Add Service"):
            st.info(
                f"Adding service {config.name} {config.version} with backend {select_backend} to {bundle.name}"
            )
            ret = infra.add_service(bundle.server.ip, config, {})
            if not ret:
                st.error("Failed to add service")

        st.write(services[selected])


tab_avail, tab_installed = st.tabs(["Available", "Installed"])
with tab_avail:
    available_services()

with tab_installed:
    installed_services()

st.divider()
if st.button("Save Infrastructure"):
    with st.spinner("Saving infrastructure..."):
        st.session_state.mlox.save_infrastructure()
