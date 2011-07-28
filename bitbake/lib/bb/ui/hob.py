#
# BitBake Graphical GTK User Interface
#
# Copyright (C) 2011        Intel Corporation
#
# Authored by Joshua Lock <josh@linux.intel.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import glib
import gobject
import gtk
from bb.ui.crumbs.tasklistmodel import TaskListModel, BuildRep
from bb.ui.crumbs.hobeventhandler import HobHandler
from bb.ui.crumbs.configurator import Configurator
from bb.ui.crumbs.hobprefs import HobPrefs
from bb.ui.crumbs.layereditor import LayerEditor
from bb.ui.crumbs.runningbuild import RunningBuildTreeView, RunningBuild
from bb.ui.crumbs.hig import CrumbsDialog
import xmlrpclib
import logging
import Queue

extraCaches = ['bb.cache_extra:HobRecipeInfo']

class MainWindow (gtk.Window):
            
    def __init__(self, taskmodel, handler, configurator, prefs, layers, mach):
        gtk.Window.__init__(self)
        # global state
        self.curr_mach = mach
        self.machine_handler_id = None
        self.image_combo_id = None
        self.generating = False
        self.files_to_clean = []
        self.selected_image = None
        self.selected_packages = None
        self.stopping = False

        self.model = taskmodel
        self.model.connect("tasklist-populated", self.update_model)
        self.model.connect("image-changed", self.image_changed_string_cb)
        self.handler = handler
        self.configurator = configurator
        self.prefs = prefs
        self.layers = layers
        self.save_path = None
        self.dirty = False

        self.connect("delete-event", self.destroy_window)
        self.set_title("Image Creator")
        self.set_icon_name("applications-development")
        self.set_default_size(1000, 650)

        self.build = RunningBuild()
        self.build.connect("build-failed", self.running_build_failed_cb)
        self.build.connect("build-complete", self.handler.build_complete_cb)
        self.build.connect("build-started", self.build_started_cb)

        self.handler.connect("build-complete", self.build_complete_cb)

        vbox = gtk.VBox(False, 0)
        vbox.set_border_width(0)
        vbox.show()
        self.add(vbox)
        self.menu = self.create_menu()
        vbox.pack_start(self.menu, False)
        createview = self.create_build_gui()
        self.back = None
        self.cancel = None
        buildview = self.view_build_gui()
        self.nb = gtk.Notebook()
        self.nb.append_page(createview)
        self.nb.append_page(buildview)
        self.nb.set_current_page(0)
        self.nb.set_show_tabs(False)
        vbox.pack_start(self.nb, expand=True, fill=True)

    def destroy_window(self, widget, event):
        self.quit()

    def menu_quit(self, action):
        self.quit()

    def quit(self):
        if self.dirty and len(self.model.contents):
            question = "Would you like to save your customisations?"
            dialog = CrumbsDialog(self, question, gtk.STOCK_DIALOG_WARNING)
            dialog.add_buttons(gtk.STOCK_NO, gtk.RESPONSE_NO,
                               gtk.STOCK_YES, gtk.RESPONSE_YES)
            resp = dialog.run()
            dialog.destroy()
            if resp == gtk.RESPONSE_YES:
                if not self.save_path:
                    self.get_save_path()

                if self.save_path:
                    self.save_recipe_file()
                    rep = self.model.get_build_rep()
                    rep.writeRecipe(self.save_path, self.model)

        gtk.main_quit()

    def scroll_tv_cb(self, model, path, it, view):
        view.scroll_to_cell(path)

    def running_build_failed_cb(self, running_build):
        # FIXME: handle this
        print("Build failed")

    def image_changed_string_cb(self, model, new_image):
        cnt = 0
        it = self.model.images.get_iter_first()
        while it:
            path = self.model.images.get_path(it)
            if self.model.images[path][self.model.COL_NAME] == new_image:
                self.image_combo.set_active(cnt)
                break
            it = self.model.images.iter_next(it)
            cnt = cnt + 1

    def image_changed_cb(self, combo):
        model = self.image_combo.get_model()
        it = self.image_combo.get_active_iter()
        if it:
            path = model.get_path(it)
            # Firstly, deselect the previous image
            userp, _ = self.model.get_selected_packages()
            self.model.reset()
            # Now select the new image and save its path in case we
            # change the image later
            self.toggle_package(path, model, image=True)
            if len(userp):
                self.model.set_selected_packages(userp)

    def reload_triggered_cb(self, handler, image, packages):
        if image:
            self.selected_image = image
        if len(packages):
            self.selected_packages = packages.split()

    def data_generated(self, handler):
        self.generating = False
        self.image_combo.set_model(self.model.images_model())
        if not self.image_combo_id:
            self.image_combo_id = self.image_combo.connect("changed", self.image_changed_cb)
        self.enable_widgets()

    def machine_combo_changed_cb(self, combo, handler):
        mach = combo.get_active_text()
        if mach != self.curr_mach:
            self.curr_mach = mach
            # Flush this straight to the file as MACHINE is changed
            # independently of other 'Preferences'
            self.configurator.setLocalConfVar('MACHINE', mach)
            self.configurator.writeLocalConf()
            handler.set_machine(mach)
            handler.reload_data()

    def update_machines(self, handler, machines):
        active = 0
        # disconnect the signal handler before updating the combo model
        if self.machine_handler_id:
            self.machine_combo.disconnect(self.machine_handler_id)
            self.machine_handler_id = None

        model = self.machine_combo.get_model()
        if model:
            model.clear()

        for machine in machines:
            self.machine_combo.append_text(machine)
            if machine == self.curr_mach:
                self.machine_combo.set_active(active)
            active = active + 1

        self.machine_handler_id = self.machine_combo.connect("changed", self.machine_combo_changed_cb, handler)

    def set_busy_cursor(self, busy=True):
        """
        Convenience method to set the cursor to a spinner when executing
        a potentially lengthy process.
        A busy value of False will set the cursor back to the default
        left pointer.
        """
        if busy:
            cursor = gtk.gdk.Cursor(gtk.gdk.WATCH)
        else:
            # TODO: presumably the default cursor is different on RTL
            # systems. Can we determine the default cursor? Or at least
            # the cursor which is set before we change it?
            cursor = gtk.gdk.Cursor(gtk.gdk.LEFT_PTR)
        window = self.get_root_window()
        window.set_cursor(cursor)

    def busy_idle_func(self):
        if self.generating:
            self.progress.set_text("Loading...")
            self.progress.pulse()
            return True
        else:
            if not self.image_combo_id:
                self.image_combo_id = self.image_combo.connect("changed", self.image_changed_cb)
            self.progress.set_text("Loaded")
            self.progress.set_fraction(0.0)
            self.set_busy_cursor(False)
            return False

    def busy(self, handler):
        self.generating = True
        self.set_busy_cursor()
        if self.image_combo_id:
            self.image_combo.disconnect(self.image_combo_id)
            self.image_combo_id = None
        self.progress.pulse()
        gobject.timeout_add (200, self.busy_idle_func)
        self.disable_widgets()

    def enable_widgets(self):
        self.menu.set_sensitive(True)
        self.machine_combo.set_sensitive(True)
        self.image_combo.set_sensitive(True)
        self.nb.set_sensitive(True)
        self.contents_tree.set_sensitive(True)

    def disable_widgets(self):
        self.menu.set_sensitive(False)
        self.machine_combo.set_sensitive(False)
        self.image_combo.set_sensitive(False)
        self.nb.set_sensitive(False)
        self.contents_tree.set_sensitive(False)

    def update_model(self, model):
        # We want the packages model to be alphabetised and sortable so create
        # a TreeModelSort to use in the view
        pkgsaz_model = gtk.TreeModelSort(self.model.packages_model())
        pkgsaz_model.set_sort_column_id(self.model.COL_NAME, gtk.SORT_ASCENDING)
        # Unset default sort func so that we only toggle between A-Z and
        # Z-A sorting
        pkgsaz_model.set_default_sort_func(None)
        self.pkgsaz_tree.set_model(pkgsaz_model)

        # We want the contents to be alphabetised so create a TreeModelSort to
        # use in the view
        contents_model = gtk.TreeModelSort(self.model.contents_model())
        contents_model.set_sort_column_id(self.model.COL_NAME, gtk.SORT_ASCENDING)
        # Unset default sort func so that we only toggle between A-Z and
        # Z-A sorting
        contents_model.set_default_sort_func(None)
        self.contents_tree.set_model(contents_model)
        self.tasks_tree.set_model(self.model.tasks_model())

        if self.selected_image:
            if self.image_combo_id:
                self.image_combo.disconnect(self.image_combo_id)
                self.image_combo_id = None
            self.model.set_selected_image(self.selected_image)
            self.selected_image = None
            if not self.image_combo_id:
                self.image_combo_id = self.image_combo.connect("changed", self.image_changed_cb)

        if self.selected_packages:
            self.model.set_selected_packages(self.selected_packages)
            self.selected_packages = None

    def reset_clicked_cb(self, button):
        lbl = "<b>Reset your selections?</b>\n\nAny new changes you have made will be lost"
        dialog = CrumbsDialog(self, lbl, gtk.STOCK_DIALOG_WARNING)
        dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        dialog.add_button("Reset", gtk.RESPONSE_OK)
        response = dialog.run()
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            self.reset_build()
            self.search.set_text("")
        return

    def reset_build(self):
        self.image_combo.disconnect(self.image_combo_id)
        self.image_combo_id = None
        self.image_combo.set_active(-1)
        self.image_combo_id = self.image_combo.connect("changed", self.image_changed_cb)
        self.model.reset()

    def layers_cb(self, action):
        resp = self.layers.run()
        self.layers.save_current_layers()
        self.layers.hide()

    def add_layer_cb(self, action):
        self.layers.find_layer(self)

    def preferences_cb(self, action):
        resp = self.prefs.run()
        self.prefs.write_changes()
        self.prefs.hide()

    def about_cb(self, action):
        about = gtk.AboutDialog()
        about.set_name("Image Creator")
        about.set_copyright("Copyright (C) 2011 Intel Corporation")
        about.set_authors(["Joshua Lock <josh@linux.intel.com>"])
        about.set_logo_icon_name("applications-development")
        about.run()
        about.destroy()

    def save_recipe_file(self):
        rep = self.model.get_build_rep()
        rep.writeRecipe(self.save_path, self.model)
        self.dirty = False

    def get_save_path(self):
        chooser = gtk.FileChooserDialog(title=None, parent=self,
                                        action=gtk.FILE_CHOOSER_ACTION_SAVE,
                                        buttons=(gtk.STOCK_CANCEL,
                                                 gtk.RESPONSE_CANCEL,
                                                 gtk.STOCK_SAVE,
                                                 gtk.RESPONSE_OK,))
        chooser.set_current_name("myimage.bb")
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            save_path = chooser.get_filename()
        else:
            save_path = None
        chooser.destroy()
        self.save_path = save_path

    def save_cb(self, action):
        if not self.save_path:
            self.get_save_path()
        if self.save_path:
            self.save_recipe_file()

    def save_as_cb(self, action):
        self.get_save_path()
        if self.save_path:
            self.save_recipe_file()

    def open_cb(self, action):
        chooser = gtk.FileChooserDialog(title=None, parent=self,
                                        action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                        buttons=(gtk.STOCK_CANCEL,
                                                 gtk.RESPONSE_CANCEL,
                                                 gtk.STOCK_OPEN,
                                                 gtk.RESPONSE_OK))
        response  = chooser.run()
        rep = BuildRep(None, None, None)
        if response == gtk.RESPONSE_OK:
            rep.loadRecipe(chooser.get_filename())
        chooser.destroy()
        self.model.load_image_rep(rep)
        self.dirty = False

    def bake_clicked_cb(self, button):
        rep = self.model.get_build_rep()
        if not rep.base_image:
            lbl = "<b>Build only packages?</b>\n\nAn image has not been selected, so only the selected packages will be built."
            dialog = CrumbsDialog(self, lbl, gtk.STOCK_DIALOG_WARNING)
            dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            dialog.add_button("Build", gtk.RESPONSE_YES)
            response = dialog.run()
            dialog.destroy()
            if response == gtk.RESPONSE_CANCEL:
                return
        else:
            # TODO: show a confirmation dialog ?
            if not self.save_path:
                import tempfile, datetime
                image_name = "hob-%s-variant-%s.bb" % (rep.base_image, datetime.date.today().isoformat())
                image_dir = os.path.join(tempfile.gettempdir(), 'hob-images')
                bb.utils.mkdirhier(image_dir)
                recipepath =  os.path.join(image_dir, image_name)
            else:
                recipepath = self.save_path

            rep.writeRecipe(recipepath, self.model)
            # In the case where we saved the file for the purpose of building
            # it we should then delete it so that the users workspace doesn't
            # contain files they haven't explicitly saved there.
            if not self.save_path:
                self.files_to_clean.append(recipepath)

            self.handler.queue_image_recipe_path(recipepath)

        self.handler.build_packages(rep.allpkgs.split(" "))
        self.nb.set_current_page(1)

    def back_button_clicked_cb(self, button):
        self.toggle_createview()

    def toggle_createview(self):
        self.build.model.clear()
        self.nb.set_current_page(0)

    def build_complete_cb(self, running_build):
        self.stopping = False
        self.back.connect("clicked", self.back_button_clicked_cb)
        self.back.set_sensitive(True)
        self.cancel.set_sensitive(False)
        for f in self.files_to_clean:
            os.remove(f)

        lbl = "<b>Build completed</b>\n\nClick 'Edit Image' to start another build or 'View Log' to view the build log."
        if self.handler.building == "image":
            deploy = self.handler.get_image_deploy_dir()
            lbl = lbl + "\n<a href=\"file://%s\" title=\"%s\">Browse folder of built images</a>." % (deploy, deploy)

        dialog = CrumbsDialog(self, lbl)
        dialog.add_button("View Log", gtk.RESPONSE_CANCEL)
        dialog.add_button("Edit Image", gtk.RESPONSE_OK)
        response = dialog.run()
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            self.toggle_createview()

    def build_started_cb(self, running_build):
        self.back.set_sensitive(False)
        self.cancel.set_sensitive(True)

    def include_gplv3_cb(self, toggle):
        excluded = toggle.get_active()
        self.handler.toggle_gplv3(excluded)

    def change_bb_threads(self, spinner):
        val = spinner.get_value_as_int()
        self.handler.set_bbthreads(val)

    def change_make_threads(self, spinner):
        val = spinner.get_value_as_int()
        self.handler.set_pmake(val)

    def toggle_toolchain(self, check):
        enabled = check.get_active()
        self.handler.toggle_toolchain(enabled)

    def toggle_headers(self, check):
        enabled = check.get_active()
        self.handler.toggle_toolchain_headers(enabled)

    def toggle_package_idle_cb(self, opath, image):
        """
        As the operations which we're calling on the model can take
        a significant amount of time (in the order of seconds) during which
        the GUI is unresponsive as the main loop is blocked perform them in
        an idle function which at least enables us to set the busy cursor
        before the UI is blocked giving the appearance of being responsive.
        """
        # Whether the item is currently included
        inc = self.model[opath][self.model.COL_INC]
        # If the item is already included, mark it for removal then
        # the sweep_up() method finds affected items and marks them
        # appropriately
        if inc:
            self.model.mark(opath)
            self.model.sweep_up()
        # If the item isn't included, mark it for inclusion
        else:
            self.model.include_item(item_path=opath,
                                    binb="User Selected",
                                    image_contents=image)

        self.set_busy_cursor(False)
        return False

    def toggle_package(self, path, model, image=False):
        inc = model[path][self.model.COL_INC]
        # Warn user before removing included packages
        if inc:
            pn = model[path][self.model.COL_NAME]
            revdeps = self.model.find_reverse_depends(pn)
            if len(revdeps):
                lbl = "<b>Remove %s?</b>\n\nThis action cannot be undone and all packages which depend on this will be removed\nPackages which depend on %s include %s." % (pn, pn, ", ".join(revdeps).rstrip(","))
            else:
                lbl = "<b>Remove %s?</b>\n\nThis action cannot be undone." % pn
            dialog = CrumbsDialog(self, lbl, gtk.STOCK_DIALOG_WARNING)
            dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            dialog.add_button("Remove", gtk.RESPONSE_OK)
            response = dialog.run()
            dialog.destroy()
            if response == gtk.RESPONSE_CANCEL:
                return

        self.set_busy_cursor()
        # Convert path to path in original model
        opath = model.convert_path_to_child_path(path)
        # This is a potentially length call which can block the
        # main loop, therefore do the work in an idle func to keep
        # the UI responsive
        glib.idle_add(self.toggle_package_idle_cb, opath, image)

        self.dirty = True

    def toggle_include_cb(self, cell, path, tv):
        model = tv.get_model()
        self.toggle_package(path, model)

    def toggle_pkg_include_cb(self, cell, path, tv):
        # there's an extra layer of models in the packages case.
        sort_model = tv.get_model()
        cpath = sort_model.convert_path_to_child_path(path)
        self.toggle_package(cpath, sort_model.get_model())

    def pkgsaz(self):
        vbox = gtk.VBox(False, 6)
        vbox.show()
        self.pkgsaz_tree = gtk.TreeView()
        self.pkgsaz_tree.set_headers_visible(True)
        self.pkgsaz_tree.set_headers_clickable(True)
        self.pkgsaz_tree.set_enable_search(True)
        self.pkgsaz_tree.set_search_column(0)
        self.pkgsaz_tree.get_selection().set_mode(gtk.SELECTION_SINGLE)

        col = gtk.TreeViewColumn('Package')
        col.set_clickable(True)
        col.set_sort_column_id(self.model.COL_NAME)
        col.set_min_width(220)
        col1 = gtk.TreeViewColumn('Description')
        col1.set_resizable(True)
        col1.set_min_width(360)
        col2 = gtk.TreeViewColumn('License')
        col2.set_resizable(True)
        col2.set_clickable(True)
        col2.set_sort_column_id(self.model.COL_LIC)
        col2.set_min_width(170)
        col3 = gtk.TreeViewColumn('Group')
        col3.set_clickable(True)
        col3.set_sort_column_id(self.model.COL_GROUP)
        col4 = gtk.TreeViewColumn('Included')
        col4.set_min_width(80)
        col4.set_max_width(90)
        col4.set_sort_column_id(self.model.COL_INC)

        self.pkgsaz_tree.append_column(col)
        self.pkgsaz_tree.append_column(col1)
        self.pkgsaz_tree.append_column(col2)
        self.pkgsaz_tree.append_column(col3)
        self.pkgsaz_tree.append_column(col4)

        cell = gtk.CellRendererText()
        cell1 = gtk.CellRendererText()
        cell1.set_property('width-chars', 20)
        cell2 = gtk.CellRendererText()
        cell2.set_property('width-chars', 20)
        cell3 = gtk.CellRendererText()
        cell4 = gtk.CellRendererToggle()
        cell4.set_property('activatable', True)
        cell4.connect("toggled", self.toggle_pkg_include_cb, self.pkgsaz_tree)

        col.pack_start(cell, True)
        col1.pack_start(cell1, True)
        col2.pack_start(cell2, True)
        col3.pack_start(cell3, True)
        col4.pack_end(cell4, True)

        col.set_attributes(cell, text=self.model.COL_NAME)
        col1.set_attributes(cell1, text=self.model.COL_DESC)
        col2.set_attributes(cell2, text=self.model.COL_LIC)
        col3.set_attributes(cell3, text=self.model.COL_GROUP)
        col4.set_attributes(cell4, active=self.model.COL_INC)

        self.pkgsaz_tree.show()

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        scroll.add(self.pkgsaz_tree)
        vbox.pack_start(scroll, True, True, 0)

        hb = gtk.HBox(False, 0)
        hb.show()
        self.search = gtk.Entry()
        self.search.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, "gtk-clear")
        self.search.connect("icon-release", self.search_entry_clear_cb)
        self.search.show()
        self.pkgsaz_tree.set_search_entry(self.search)
        hb.pack_end(self.search, False, False, 0)
        label = gtk.Label("Search packages:")
        label.show()
        hb.pack_end(label, False, False, 6)
        vbox.pack_start(hb, False, False, 0)

        return vbox

    def search_entry_clear_cb(self, entry, icon_pos, event):
        entry.set_text("")

    def tasks(self):
        vbox = gtk.VBox(False, 6)
        vbox.show()
        self.tasks_tree = gtk.TreeView()
        self.tasks_tree.set_headers_visible(True)
        self.tasks_tree.set_headers_clickable(False)
        self.tasks_tree.set_enable_search(True)
        self.tasks_tree.set_search_column(0)
        self.tasks_tree.get_selection().set_mode(gtk.SELECTION_SINGLE)

        col = gtk.TreeViewColumn('Package Collection')
        col.set_min_width(430)
        col1 = gtk.TreeViewColumn('Description')
        col1.set_min_width(430)
        col2 = gtk.TreeViewColumn('Include')
        col2.set_min_width(70)
        col2.set_max_width(80)

        self.tasks_tree.append_column(col)
        self.tasks_tree.append_column(col1)
        self.tasks_tree.append_column(col2)

        cell = gtk.CellRendererText()
        cell1 = gtk.CellRendererText()
        cell2 = gtk.CellRendererToggle()
        cell2.set_property('activatable', True)
        cell2.connect("toggled", self.toggle_include_cb, self.tasks_tree)

        col.pack_start(cell, True)
        col1.pack_start(cell1, True)
        col2.pack_end(cell2, True)

        col.set_attributes(cell, text=self.model.COL_NAME)
        col1.set_attributes(cell1, text=self.model.COL_DESC)
        col2.set_attributes(cell2, active=self.model.COL_INC)

        self.tasks_tree.show()

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        scroll.add(self.tasks_tree)
        vbox.pack_start(scroll, True, True, 0)

        hb = gtk.HBox(False, 0)
        hb.show()
        search = gtk.Entry()
        search.show()
        self.tasks_tree.set_search_entry(search)
        hb.pack_end(search, False, False, 0)
        label = gtk.Label("Search collections:")
        label.show()
        hb.pack_end(label, False, False, 6)
        vbox.pack_start(hb, False, False, 0)

        return vbox

    def cancel_build(self, button):
        if self.stopping:
            lbl = "<b>Force Stop build?</b>\nYou've already selected Stop once,"
            lbl = lbl + " would you like to 'Force Stop' the build?\n\n"
            lbl = lbl + "This will stop the build as quickly as possible but may"
            lbl = lbl + " well leave your build directory in an  unusable state"
            lbl = lbl + " that requires manual steps to fix.\n"
            dialog = CrumbsDialog(self, lbl, gtk.STOCK_DIALOG_WARNING)
            dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            dialog.add_button("Force Stop", gtk.RESPONSE_YES)
        else:
            lbl = "<b>Stop build?</b>\n\nAre you sure you want to stop this"
            lbl = lbl + " build?\n\n'Force Stop' will stop the build as quickly as"
            lbl = lbl + " possible but may well leave your build directory in an"
            lbl = lbl + " unusable state that requires manual steps to fix.\n\n"
            lbl = lbl + "'Stop' will stop the build as soon as all in"
            lbl = lbl + " progress build tasks are finished. However if a"
            lbl = lbl + " lengthy compilation phase is in progress this may take"
            lbl = lbl + " some time."
            dialog = CrumbsDialog(self, lbl, gtk.STOCK_DIALOG_WARNING)
            dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            dialog.add_button("Stop", gtk.RESPONSE_OK)
            dialog.add_button("Force Stop", gtk.RESPONSE_YES)
        response = dialog.run()
        dialog.destroy()
        if response != gtk.RESPONSE_CANCEL:
            self.stopping = True
        if response == gtk.RESPONSE_OK:
            self.handler.cancel_build()
        elif response == gtk.RESPONSE_YES:
            self.handler.cancel_build(True)

    def view_build_gui(self):
        vbox = gtk.VBox(False, 12)
        vbox.set_border_width(6)
        vbox.show()
        build_tv = RunningBuildTreeView()
        build_tv.show()
        build_tv.set_model(self.build.model)
        self.build.model.connect("row-inserted", self.scroll_tv_cb, build_tv)
        scrolled_view = gtk.ScrolledWindow ()
        scrolled_view.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_view.add(build_tv)
        scrolled_view.show()
        vbox.pack_start(scrolled_view, expand=True, fill=True)
        hbox = gtk.HBox(False, 12)
        hbox.show()
        vbox.pack_start(hbox, expand=False, fill=False)
        self.back = gtk.Button("Back")
        self.back.show()
        self.back.set_sensitive(False)
        hbox.pack_start(self.back, expand=False, fill=False)
        self.cancel = gtk.Button("Stop Build")
        self.cancel.connect("clicked", self.cancel_build)
        self.cancel.show()
        hbox.pack_end(self.cancel, expand=False, fill=False)

        return vbox

    def create_menu(self):
        menu_items = '''<ui>
        <menubar name="MenuBar">
          <menu action="File">
            <menuitem action="Save"/>
            <menuitem action="Save As"/>
            <menuitem action="Open"/>
            <separator/>
            <menuitem action="AddLayer" label="Add Layer"/>
            <separator/>
            <menuitem action="Quit"/>
          </menu>
          <menu action="Edit">
            <menuitem action="Layers" label="Layers"/>
            <menuitem action="Preferences"/>
          </menu>
          <menu action="Help">
            <menuitem action="About"/>
          </menu>
        </menubar>
        </ui>'''

        uimanager = gtk.UIManager()
        accel = uimanager.get_accel_group()
        self.add_accel_group(accel)

        actions = gtk.ActionGroup('ImageCreator')
        self.actions = actions
        actions.add_actions([('Quit', gtk.STOCK_QUIT, None, None,
                              None, self.menu_quit,),
                             ('File', None, '_File'),
                             ('Save', gtk.STOCK_SAVE, None, None, None, self.save_cb),
                             ('Save As', gtk.STOCK_SAVE_AS, None, None, None, self.save_as_cb),
                             ('Open', gtk.STOCK_OPEN, None, None, None, self.open_cb),
                             ('AddLayer', None, 'Add Layer', None, None, self.add_layer_cb),
                             ('Edit', None, '_Edit'),
                             ('Help', None, '_Help'),
                             ('Layers', None, 'Layers', None, None, self.layers_cb),
                             ('Preferences', gtk.STOCK_PREFERENCES, None, None, None, self.preferences_cb),
                             ('About', gtk.STOCK_ABOUT, None, None, None, self.about_cb)])
        uimanager.insert_action_group(actions, 0)
        uimanager.add_ui_from_string(menu_items)

        menubar = uimanager.get_widget('/MenuBar')
        menubar.show_all()

        return menubar
    
    def create_build_gui(self):
        vbox = gtk.VBox(False, 12)
        vbox.set_border_width(6)
        vbox.show()
        
        hbox = gtk.HBox(False, 12)
        hbox.show()
        vbox.pack_start(hbox, expand=False, fill=False)

        label = gtk.Label("Machine:")
        label.show()
        hbox.pack_start(label, expand=False, fill=False, padding=6)
        self.machine_combo = gtk.combo_box_new_text()
        self.machine_combo.show()
        self.machine_combo.set_tooltip_text("Selects the architecture of the target board for which you would like to build an image.")
        hbox.pack_start(self.machine_combo, expand=False, fill=False, padding=6)
        label = gtk.Label("Base image:")
        label.show()
        hbox.pack_start(label, expand=False, fill=False, padding=6)
        self.image_combo = gtk.ComboBox()
        self.image_combo.show()
        self.image_combo.set_tooltip_text("Selects the image on which to base the created image")
        image_combo_cell = gtk.CellRendererText()
        self.image_combo.pack_start(image_combo_cell, True)
        self.image_combo.add_attribute(image_combo_cell, 'text', self.model.COL_NAME)
        hbox.pack_start(self.image_combo, expand=False, fill=False, padding=6)
        self.progress = gtk.ProgressBar()
        self.progress.set_size_request(250, -1)
        hbox.pack_end(self.progress, expand=False, fill=False, padding=6)

        ins = gtk.Notebook()
        vbox.pack_start(ins, expand=True, fill=True)
        ins.set_show_tabs(True)
        label = gtk.Label("Packages")
        label.show()
        ins.append_page(self.pkgsaz(), tab_label=label)
        label = gtk.Label("Package Collections")
        label.show()
        ins.append_page(self.tasks(), tab_label=label)
        ins.set_current_page(0)
        ins.show_all()

        label = gtk.Label("Image contents:")
        self.model.connect("contents-changed", self.update_package_count_cb, label)
        label.set_property("xalign", 0.00)
        label.show()
        vbox.pack_start(label, expand=False, fill=False, padding=6)
        con = self.contents()
        con.show()
        vbox.pack_start(con, expand=True, fill=True)

        bbox = gtk.HButtonBox()
        bbox.set_spacing(12)
        bbox.set_layout(gtk.BUTTONBOX_END)
        bbox.show()
        vbox.pack_start(bbox, expand=False, fill=False)
        reset = gtk.Button("Reset")
        reset.connect("clicked", self.reset_clicked_cb)
        reset.show()
        bbox.add(reset)
        bake = gtk.Button("Bake")
        bake.connect("clicked", self.bake_clicked_cb)
        bake.show()
        bbox.add(bake)

        return vbox

    def update_package_count_cb(self, model, count, label):
        lbl = "Image contents (%s packages):" % count
        label.set_text(lbl)

    def contents(self):
        self.contents_tree = gtk.TreeView()
        self.contents_tree.set_headers_visible(True)
        self.contents_tree.get_selection().set_mode(gtk.SELECTION_SINGLE)

        # allow searching in the package column
        self.contents_tree.set_search_column(0)
        self.contents_tree.set_enable_search(True)

        col = gtk.TreeViewColumn('Package')
        col.set_sort_column_id(0)
        col.set_min_width(430)
        col1 = gtk.TreeViewColumn('Brought in by')
        col1.set_resizable(True)
        col1.set_min_width(430)

        self.contents_tree.append_column(col)
        self.contents_tree.append_column(col1)

        cell = gtk.CellRendererText()
        cell1 = gtk.CellRendererText()
        cell1.set_property('width-chars', 20)

        col.pack_start(cell, True)
        col1.pack_start(cell1, True)

        col.set_attributes(cell, text=self.model.COL_NAME)
        col1.set_attributes(cell1, text=self.model.COL_BINB)

        self.contents_tree.show()

        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER, gtk.POLICY_ALWAYS)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        scroll.add(self.contents_tree)

        return scroll

def main (server, eventHandler):
    import multiprocessing
    cpu_cnt = multiprocessing.cpu_count()

    gobject.threads_init()

    taskmodel = TaskListModel()
    configurator = Configurator()
    handler = HobHandler(taskmodel, server)
    mach = server.runCommand(["getVariable", "MACHINE"])
    sdk_mach = server.runCommand(["getVariable", "SDKMACHINE"])
    # If SDKMACHINE not set the default SDK_ARCH is used so we
    # should represent that in the GUI
    if not sdk_mach:
        sdk_mach = server.runCommand(["getVariable", "SDK_ARCH"])
    distro = server.runCommand(["getVariable", "DISTRO"])
    bbthread = server.runCommand(["getVariable", "BB_NUMBER_THREADS"])
    if not bbthread:
        bbthread = cpu_cnt
        handler.set_bbthreads(cpu_cnt)
    else:
        bbthread = int(bbthread)
    pmake = server.runCommand(["getVariable", "PARALLEL_MAKE"])
    if not pmake:
        pmake = cpu_cnt
        handler.set_pmake(cpu_cnt)
    else:
        # The PARALLEL_MAKE variable will be of the format: "-j 3" and we only
        # want a number for the spinner, so strip everything from the variable
        # up to and including the space
        pmake = int(pmake.lstrip("-j "))

    image_types = server.runCommand(["getVariable", "IMAGE_TYPES"])

    pclasses = server.runCommand(["getVariable", "PACKAGE_CLASSES"]).split(" ")
    # NOTE: we're only supporting one value for PACKAGE_CLASSES being set
    # this seems OK because we're using the first package format set in
    # PACKAGE_CLASSES and that's the package manager used for the rootfs
    pkg, sep, pclass = pclasses[0].rpartition("_")

    prefs = HobPrefs(configurator, handler, sdk_mach, distro, pclass, cpu_cnt,
                     pmake, bbthread, image_types)
    layers = LayerEditor(configurator, None)
    window = MainWindow(taskmodel, handler, configurator, prefs, layers, mach)
    prefs.set_parent_window(window)
    layers.set_parent_window(window)
    window.show_all ()
    handler.connect("machines-updated", window.update_machines)
    handler.connect("sdk-machines-updated", prefs.update_sdk_machines)
    handler.connect("distros-updated", prefs.update_distros)
    handler.connect("package-formats-found", prefs.update_package_formats)
    handler.connect("generating-data", window.busy)
    handler.connect("data-generated", window.data_generated)
    handler.connect("reload-triggered", window.reload_triggered_cb)
    configurator.connect("layers-loaded", layers.load_current_layers)
    configurator.connect("layers-changed", handler.reload_data)
    handler.connect("config-found", configurator.configFound)

    try:
        # kick the while thing off
        handler.current_command = "findConfigFilePathLocal"
        server.runCommand(["findConfigFilePath", "local.conf"])
    except xmlrpclib.Fault:
        print("XMLRPC Fault getting commandline:\n %s" % x)
        return 1

    # This timeout function regularly probes the event queue to find out if we
    # have any messages waiting for us.
    gobject.timeout_add (100,
                         handler.event_handle_idle_func,
                         eventHandler,
                         window.build,
                         window.progress)

    try:
        gtk.main()
    except EnvironmentError as ioerror:
        # ignore interrupted io
        if ioerror.args[0] == 4:
            pass
    finally:
        server.runCommand(["stateStop"])

