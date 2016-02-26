# -*- coding: utf-8 -*-

import argparse
import sys

from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


class Group(VerdiCommandWithSubcommands):
    """
    Setup and manage groups

    There is a list of subcommands to perform specific operation on groups.
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called:
        list.
        """
        self.valid_subcommands = {
            'list': (self.group_list, self.complete_none),
            'show': (self.group_show, self.complete_none),
            'description': (self.group_description, self.complete_none),
            'create': (self.group_create, self.complete_none),
            'delete': (self.group_delete, self.complete_none),
            'addnodes': (self.group_addnodes, self.complete_none),
            'removenodes': (self.group_removenodes, self.complete_none),
        }

    def group_create(self, *args):
        """
        Create a new empty group.
        """
        if not is_dbenv_loaded():
            load_dbenv()

        import argparse
        from aiida.orm import Group as G

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Create a new empty group.')
        parser.add_argument('GROUPNAME', help="The name of the new group")

        args = list(args)
        parsed_args = parser.parse_args(args)

        group_name = parsed_args.GROUPNAME

        group, created = G.get_or_create(name=group_name)

        if created:
            print "Group created with PK = {} and name '{}'".format(
                group.pk, group.name)
        else:
            print "Group '{}' already exists, PK = {}".format(
                group.name, group.pk)

    def group_delete(self, *args):
        """
        Delete an existing group.
        """
        if not is_dbenv_loaded():
            load_dbenv()

        import argparse
        from aiida.common.exceptions import NotExistent
        from aiida.orm import Group as G
        from aiida.cmdline import wait_for_confirmation

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Delete an existing group.')
        parser.add_argument('-f', '--force',
                            dest='force', action='store_true',
                            help="Force deletion of the group even if it "
                            "is not empty. Note that this deletes only the "
                            "group and not the nodes.")
        parser.add_argument('GROUP', help="The name or PK of the group to delete")
        parser.set_defaults(force=False)

        args = list(args)
        parsed_args = parser.parse_args(args)

        group = parsed_args.GROUP
        force = parsed_args.force
        try:
            group_pk = int(group)
        except ValueError:
            group_pk = None
            group_name = group

        if group_pk is not None:
            try:
                group = G(dbgroup=group_pk)
            except NotExistent as e:
                print >> sys.stderr, "Error: {}.".format(e.message)
                sys.exit(1)
        else:
            try:
                group = G.get_from_string(group_name)
            except NotExistent as e:
                print >> sys.stderr, "Error: {}.".format(e.message)
                sys.exit(1)

        group_pk = group.pk
        group_name = group.name

        num_nodes = len(group.nodes)
        if num_nodes > 0 and not force:
            print >> sys.stderr, ("Group '{}' is not empty (it contains {} "
                "nodes). Pass the -f option if you really want to delete "
                "it.".format(group_name, num_nodes))
            sys.exit(1)

        sys.stderr.write("Are you sure to kill the group with PK = {} ({})? "
            "[Y/N] ".format(group_pk, group_name))
        if not wait_for_confirmation():
            sys.exit(0)

        group.delete()
        print "Group '{}' (PK={}) deleted.".format(group_name, group_pk)

    def group_show(self, *args):
        """
        Show information on a given group. Pass the PK as a parameter.
        """
        if not is_dbenv_loaded():
            load_dbenv()

        import argparse
        from aiida.common.exceptions import NotExistent
        from aiida.orm import Group as G
        from aiida.common.utils import str_timedelta
        from aiida.utils import timezone
        from aiida.orm.node import from_type_to_pluginclassname

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Information on a given AiiDA group.')
        parser.add_argument('-r', '--raw',
                            dest='raw', action='store_true',
                            help="Show only a space-separated list of PKs of "
                            "the calculations in the group")
        parser.add_argument('-u', '--uuid',
                            dest='uuid', action='store_true',
                            help="Show UUIDs together with PKs. Note: if the "
                                 "--raw option is also passed, PKs are not "
                                 "printed, but oly UUIDs.")
        parser.add_argument('GROUP', help="The PK of the group to show")
        parser.set_defaults(raw=False)
        parser.set_defaults(uuid=False)

        args = list(args)
        parsed_args = parser.parse_args(args)

        group = parsed_args.GROUP
        try:
            group_pk = int(group)
        except ValueError:
            group_pk = None
            group_name = group

        if group_pk is not None:
            try:
                group = G(dbgroup=group_pk)
            except NotExistent as e:
                print >> sys.stderr, "Error: {}.".format(e.message)
                sys.exit(1)
        else:
            try:
                group = G.get_from_string(group_name)
            except NotExistent as e:
                print >> sys.stderr, "Error: {}.".format(e.message)
                sys.exit(1)

        group_pk = group.pk
        group_name = group.name

        if parsed_args.raw:
            if parsed_args.uuid:
                print " ".join(str(_.uuid) for _ in group.nodes)
            else:
                print " ".join(str(_.pk) for _ in group.nodes)
        else:
            type_string = group.type_string
            desc = group.description
            now = timezone.now()

            print "# Group name: {}".format(group.name)
            print "# Group type: {}".format(type_string if type_string
                                            else "<user-defined>")
            print "# Group description: {}".format(desc if desc else
                                                   "<no description>")
            print "# Nodes:"
            uuid_string = ""
            for n in group.nodes:
                if parsed_args.uuid:
                    uuid_string = "{} - ".format(n.uuid)
                print "* {}{} - {} - {}".format(
                    uuid_string, n.pk,
                    from_type_to_pluginclassname(n.dbnode.type).rsplit(".", 1)[1],
                    str_timedelta(now - n.ctime, short=True,
                                  negative_to_zero=True))

    def group_addnodes(self, *args):
        """
        Add nodes to a given group.
        """
        from aiida.cmdline import delayed_load_node as load_node
        from aiida.cmdline import wait_for_confirmation

        if not is_dbenv_loaded():
            load_dbenv()

        import argparse
        from aiida.common.exceptions import NotExistent
        from aiida.orm import Group as G

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Add nodes to a given AiiDA group.')
        parser.add_argument('-g', '--group',
                            dest='group',
                            required=True,
                            help="The name or PK of the group you want to add "
                            "a node to.")
        parser.add_argument('nodes', nargs='+',
                            help="The PK or UUID of the nodes to add")
        parser.set_defaults(raw=False)

        args = list(args)
        parsed_args = parser.parse_args(args)

        group = parsed_args.group
        try:
            group_pk = int(group)
        except ValueError:
            group_pk = None
            group_name = group

        if group_pk is not None:
            try:
                group = G(dbgroup=group_pk)
            except NotExistent as e:
                print >> sys.stderr, "Error: {}.".format(e.message)
                sys.exit(1)
        else:
            try:
                group = G.get_from_string(group_name)
            except NotExistent as e:
                print >> sys.stderr, "Error: {}.".format(e.message)
                sys.exit(1)

        group_pk = group.pk
        group_name = group.name

        nodes = []
        for node in parsed_args.nodes:
            try:
                node = int(node)
            except ValueError:
                pass # I leave it as a string and let load_node complain
                     # if it is not a UUID
            try:
                nodes.append(load_node(node))
            except NotExistent as e:
                print >> sys.stderr, "Error: {}.".format(e.message)
                sys.exit(1)


        sys.stderr.write("Are you sure to add {} nodes the group with PK = {} "
                         "({})? [Y/N] ".format(len(nodes), group_pk, group_name))
        if not wait_for_confirmation():
            sys.exit(0)

        group.add_nodes(nodes)


    def group_removenodes(self, *args):
        """
        Remove nodes from a given group.
        """
        from aiida.cmdline import delayed_load_node as load_node
        from aiida.cmdline import wait_for_confirmation

        if not is_dbenv_loaded():
            load_dbenv()

        import argparse
        from aiida.common.exceptions import NotExistent
        from aiida.orm import Group as G

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Remove nodes from a given AiiDA group.')
        parser.add_argument('-g', '--group',
                            dest='group',
                            required=True,
                            help="The name or PK of the group you want to "
                            "remove a node from.")
        parser.add_argument('nodes', nargs='+',
                            help="The PK or UUID of the nodes to remove. An "
                            "error is raised if the node does not exist. "
                            "No message is shown if the node does not belong "
                            "to the group.")
        parser.set_defaults(raw=False)

        args = list(args)
        parsed_args = parser.parse_args(args)

        group = parsed_args.group
        try:
            group_pk = int(group)
        except ValueError:
            group_pk = None
            group_name = group

        if group_pk is not None:
            try:
                group = G(dbgroup=group_pk)
            except NotExistent as e:
                print >> sys.stderr, "Error: {}.".format(e.message)
                sys.exit(1)
        else:
            try:
                group = G.get_from_string(group_name)
            except NotExistent as e:
                print >> sys.stderr, "Error: {}.".format(e.message)
                sys.exit(1)

        group_pk = group.pk
        group_name = group.name

        nodes = []
        for node in parsed_args.nodes:
            try:
                node = int(node)
            except ValueError:
                pass # I leave it as a string and let load_node complain
                     # if it is not a UUID
            try:
                nodes.append(load_node(node))
            except NotExistent as e:
                print >> sys.stderr, "Error: {}.".format(e.message)
                sys.exit(1)

        sys.stderr.write("Are you sure to remove {} nodes from the group "
                         "with PK = {} "
                         "({})? [Y/N] ".format(len(nodes), group_pk, group_name))
        if not wait_for_confirmation():
            sys.exit(0)

        group.remove_nodes(nodes)


    def group_description(self, *args):
        """
        Edit the group description.
        """
        if not is_dbenv_loaded():
            load_dbenv()

        import argparse
        from aiida.orm import Group as G
        from aiida.common.exceptions import NotExistent

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Change the description of a given group.')
        parser.add_argument('PK',type=int, help="The PK of the group for which "
                            "you want to edit the description")
        parser.add_argument('description',type=str,
                            help="The new description. If not provided, "
                            "just show the current description.")

        args = list(args)
        parsed_args = parser.parse_args(args)

        group_pk = parsed_args.PK
        try:
            group = G(dbgroup=group_pk)
        except NotExistent as e:
            print >> sys.stderr, "Error: {}.".format(e.message)
            sys.exit(1)

        group.description = parsed_args.description



    def group_list(self, *args):
        """
        Print a list of groups in the DB.
        """
        if not is_dbenv_loaded():
            load_dbenv()

        from aiida.orm.group import get_group_type_mapping
        from aiida.backends.utils import get_automatic_user, get_group_list

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='List AiiDA user-defined groups.')
        exclusive_group = parser.add_mutually_exclusive_group()
        exclusive_group.add_argument('-A', '--all-users',
                                     dest='all_users', action='store_true',
                                     help="Show groups for all users, rather than only for the current user")
        exclusive_group.add_argument('-u', '--user', metavar='USER_EMAIL',
                                     help="Add a filter to show only groups belonging to a specific user",
                                     action='store', type=str)
        parser.add_argument('-t', '--type', metavar='TYPE',
                            help="Show groups of a specific type, instead of user-defined groups",
                            action='store', type=str)
        parser.add_argument('-d', '--with-description',
                            dest='with_description', action='store_true',
                            help="Show also the group description")
        parser.add_argument('-p', '--past-days', metavar='N',
                            help="add a filter to show only groups created in the past N days",
                            action='store', type=int)
        parser.add_argument('-s', '--startswith', metavar='STRING', default=None,
                            help="add a filter to show only groups for which the name begins with STRING",
                            action='store', type=str)
        parser.add_argument('-e', '--endswith', metavar='STRING', default=None,
                            help="add a filter to show only groups for which the name ends with STRING",
                            action='store', type=str)
        parser.add_argument('-c', '--contains', metavar='STRING', default=None,
                            help="add a filter to show only groups for which the name contains STRING",
                            action='store', type=str)
        parser.set_defaults(all_users=False)
        parser.set_defaults(with_description=False)

        args = list(args)
        parsed_args = parser.parse_args(args)

        if parsed_args.all_users:
            user = None
        else:
            if parsed_args.user:
                user = parsed_args.user
            else:
                # By default: only groups of this user
                user = get_automatic_user()

        if parsed_args.type is None:
            type_string = ""
        else:
            try:
                type_string = get_group_type_mapping()[parsed_args.type]
            except KeyError:
                print >> sys.stderr, "Invalid group type. Valid group types are:"
                print >> sys.stderr, ",".join(sorted(
                    get_group_type_mapping().keys()))
                sys.exit(1)

        name_filters = dict((k, getattr(parsed_args, k))
                            for k in ['startswith','endswith','contains'])

        groups = get_group_list(user, type_string,
                                n_days_ago=parsed_args.past_days,
                                name_filters=name_filters)


        # nice formatting
        # gather all info

        # get the max length
        max_pks_len = max([len(i[0]) for i in groups]) if groups else 4
        max_names_len = max([len(i[1]) for i in groups]) if groups else 4
        max_nodes_len = max([len(str(i[2])) for i in groups]) if groups else 4
        max_users_len = max([len(i[3]) for i in groups]) if groups else 4

        tolerated_name_length = (80 - 11 - max_nodes_len -
                                 max_users_len - max_pks_len - 1)

        #print max_names_len, tolerated_name_length


        if parsed_args.with_description:
            print "# Format: PK | GroupName | NumNodes | User | Description"

            fmt_string = "* {:<" + str(max_pks_len) + "} | "
            fmt_string += "{:<" + str(max_names_len) + "} | "
            fmt_string += "{:" + str(max_nodes_len) + "d} | "
            fmt_string += "{:" + str(max_users_len) + "s} | {}"

            for pk, nam, nod, usr, desc in groups:
                print fmt_string.format(pk, nam, nod, usr, desc)

        else:
            print "# Format: PK | GroupName | NumNodes | User"

            first_fmt_string = "* {:<" + str(max_pks_len) + "} | "
            first_fmt_string += "{:<" + str(tolerated_name_length) + "} | "
            first_fmt_string += "{:" + str(max_nodes_len) + "d} | "
            first_fmt_string += "{:" + str(max_users_len) + "s}"

            extra_fmt_string = "  " + " " * max_pks_len  + " | "
            extra_fmt_string += "{:<" + str(tolerated_name_length) + "} | "
            extra_fmt_string += " " * max_nodes_len + " | "
            extra_fmt_string += " " * max_users_len

            for pk, nam, nod, usr, _ in groups:
                the_nams = [nam[i:i + tolerated_name_length] for i in range(0, len(nam), tolerated_name_length)]
                print first_fmt_string.format(pk, the_nams[0], nod, usr)
                for i in the_nams[1:]:
                    print extra_fmt_string.format(i)































