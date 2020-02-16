# Default package import
import os
import sys


# ProtonVPN base CLI package import
from protonvpn_cli.constants import (USER, CONFIG_FILE, CONFIG_DIR, VERSION)
from protonvpn_cli import cli
from protonvpn_cli import connection

# ProtonVPN helper funcitons
from protonvpn_cli.utils import (
    get_config_value,
    set_config_value,
    check_root,
)

# Custom helper functions
from .utils.utils import (
    update_labels_status,
    populate_server_list,
    prepare_initilizer,
    load_on_start,
    load_configurations
)

# PyGObject import
import gi

# Gtk3 import
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class Handler:
    """Handler that has all callback functions.
    """
    def __init__(self, interface):
        self.interface = interface

    # Login BUTTON HANDLER
    def on_login_button_clicked(self, button):
        login_window = self.interface.get_object("LoginWindow")
        username_field = self.interface.get_object('username_field').get_text()
        password_field = self.interface.get_object('password_field').get_text()
        
        user_data = prepare_initilizer(username_field, password_field, self.interface)

        if not cli.init_cli(gui_enabled=True, gui_user_input=user_data):
            return

        user_window = self.interface.get_object("Dashboard")
        server_list_object = self.interface.get_object("ServerListStore")

        populate_server_list(server_list_object)
        login_window.destroy()
        user_window.show()

    # Dashboard BUTTON HANDLERS
    def connect_to_selected_server_button_clicked(self, button):
        selected_server = ''
        protocol = get_config_value("USER", "default_protocol")

        server_list = self.interface.get_object("ServerList").get_selection() 
        (model, pathlist) = server_list.get_selected_rows()
        for path in pathlist :
            tree_iter = model.get_iter(path)
            # the second param of get_value() specifies the column number, starting at 0
            selected_server = model.get_value(tree_iter, 1)
        connection.openvpn_connect(selected_server, protocol)
        update_labels_status(self.interface)
        
    def quick_connect_button_clicked(self, button):
        """Connecte to the fastest server
        """
        protocol = get_config_value("USER", "default_protocol")
        connection.fastest(protocol, gui_enabled=True)
        update_labels_status(self.interface)
    
    def last_connect_button_clicked(self, button):
        """Reconnects to previously connected server
        """        
        connection.reconnect()
        update_labels_status(self.interface)

    def random_connect_button_clicked(self, button):
        """Connects to a random server
        """
        protocol = get_config_value("USER", "default_protocol")
        connection.random_c(protocol)
        update_labels_status(self.interface)

    def disconnect_button_clicked(self, button):
        """Disconnects any existing connections
        """
        connection.disconnect()
        update_labels_status(self.interface)
        
    def refresh_server_list_button_clicked(self, button):
        """Button to refresh/repopulate server list
        """
        server_list_object = self.interface.get_object("ServerListStore")
        populate_server_list(server_list_object)

    def about_menu_button_clicked(self, button):
        """Button to open About dialog
        """
        about_dialog = self.interface.get_object("AboutDialog")
        version = "v."+VERSION
        about_dialog.set_version(version)
        about_dialog.show()

    def configuration_menu_button_clicked(self, button):
        """Button to open Configurations window
        """
        load_configurations(self.interface)

    # Dashboard TOGGLE HANDLERS
    def killswitch_toggle_button_clicked(self, toggle):
        """Kill switch toggle button. To enable or disable killswitch.
        """
        print("To-do killswitch")
        # print("CLICKED", toggle.get_active())

        # Creates infinite loop, need to find a workaround
        # if toggle.get_active() == True:
        #     set_config_value("USER", "killswitch", 0)
        #     toggle.set_active(False)
        # else:
        #     set_config_value("USER", "killswitch", 1)
        #     toggle.set_active(True)
        # Check if iptables are backed up; represents killswitch
        # if os.path.isfile(os.path.join(CONFIG_DIR, "iptables.backup")):
        #     killswitch_on = True
        # else:
        #     killswitch_on = False
        # killswitch_status = "Enabled" if killswitch_on else "Disabled"
        
    def killswitch_toggle_button_activated(self, toggle):
        """Testing feature.
        """
        print("ACTIVATED", toggle.get_active())
       

    def start_on_boot_toogle_button_clicked(self, checkbox):
        """Start on boot toggle button. To enable or disable start on boot.
        """
        # try with a subprocess, if it fails then it is not systemd cat /proc/1/comm
        print("To-do start on boot")

    # To avoid getting the Preferences window destroyed and not being re-rendered again
    def ConfigurationsWindow_delete_event(self, object, event):
        if object.get_property("visible") == True:
            object.hide()
            return True
    
    # To avoid getting the About window destroyed and not being re-rendered again
    def AboutDialog_delete_event(self, object, event):
        if object.get_property("visible") == True:
            object.hide()
            return True

    # Preferences/Configuration menu HANDLERS
    def update_user_pass_button_clicked(self, button):
        username_field = self.interface.get_object("update_username_input")
        password_field = self.interface.get_object("update_password_input")

        username_text = username_field.get_text().strip()
        password_text = password_field.get_text().strip()

        if len(username_text) == 0 or len(password_text) == 0:
            print("Both field need to be filled")
            return

        cli.set_username_password(write=True, gui_enabled=True, user_data=(username_text, password_text))
        password_field.set_text("")

    def dns_preferens_combobox_changed(self, button):
        """Event handler that is triggered whenever combo box value is changed.
        """
        # DNS ComboBox
        # 0 - Leak Protection Enabled
        # 1 - Custom DNS
        # 2 - None

        dns_custom_input = self.interface.get_object("dns_custom_input")

        if button.get_active() == 0 or button.get_active() == 2:
            dns_custom_input.set_property('sensitive', False)
        else:
            dns_custom_input.set_property('sensitive', True)

    def update_dns_button_clicked(self, button):
        dns_combobox = self.interface.get_object("dns_preferens_combobox")

        dns_leak_protection = 1
        custom_dns = None
        if (not dns_combobox.get_active() == 0) and (not dns_combobox.get_active() == 2):
            dns_leak_protection = 0
            custom_dns = self.interface.get_object("dns_custom_input").get_text()
        elif dns_combobox.get_active() == 2:
            dns_leak_protection = 0
        
        cli.set_dns_protection(gui_enabled=True, dns_settings=(dns_leak_protection, custom_dns))

    def update_pvpn_plan_button_clicked(self, button):
        protonvpn_plan = 0
        protonvpn_plans = {
            1: self.interface.get_object("member_free_update_checkbox").get_active(),
            2: self.interface.get_object("member_basic_update_checkbox").get_active(),
            3: self.interface.get_object("member_plus_update_checkbox").get_active(),
            4: self.interface.get_object("member_visionary_update_checkbox").get_active()
        }

        for k,v in protonvpn_plans.items():
            if v == True:
                protonvpn_plan = int(k)
                break
            
        cli.set_protonvpn_tier(write=True, gui_enabled=True, tier=protonvpn_plan)        

    def update_def_protocol_button_clicked(self, button):
        openvpn_protocol = 'tcp' if self.interface.get_object('protocol_tcp_update_checkbox').get_active() else 'udp'
        
        cli.set_default_protocol(write=True, gui_enabled=True, protoc=openvpn_protocol)

    def update_split_tunneling_button_clicked(self, button):
        print("To-do split tunnel")

    def purge_configurations_button_clicked(self, button):
        # To-do: Confirm prior to allowing user to do this
        cli.purge_configuration(gui_enabled=True)

class initialize_gui:
    """Initializes a GUI
    -----
    The GUI only makes external calls to the cli commands.
    -----
    Will request for the same data protonvpn init to initialize a user:
    -Username
    -Password
    -Plan
    -Protocol

    There are two ways of starting this GUI, either by reversing the commented code so that it can be launched as part of the CLI: 
    ---
    -protonvpn gui:
        This will start from within the main CLI menu. Gui is invoked through cli()

    Or leave it be as it is, and configuration is setup during installation with "pip3 install -e .", this way it can be launched as a separte command from the usual CLI:
    -protonvpn-gui:
        This will start the GUI without invoking cli()
    """
    def __init__(self):
        check_root()
        interface = Gtk.Builder()
        path = os.path.expanduser("~{0}".format(USER))
        path = path + "/protonvpn-cli-ng/gui/main.glade"

        interface.add_from_file(path)
        interface.connect_signals(Handler(interface))

        if not os.path.isfile(CONFIG_FILE):
            window = interface.get_object("LoginWindow")
        else:
            window = interface.get_object("Dashboard")
            load_on_start(interface)
        
        window.show()
        Gtk.main()