<template>
  <div>
    <template v-if="isBusy">
      <b-row>
        <b-col class="text-center" v-if="isBusy" style="margin-bottom: 20px;">
          <b-spinner class="align-middle" label="Loading..."></b-spinner>
          <strong>Loading...</strong>
        </b-col>
      </b-row>
    </template>
    <template v-else>
      <h1 span v-if="mode=='edit'">Edit user</h1>
      <h1 v-else>New user</h1>
      <b-form class="form-horizontal" @submit.stop.prevent="updateUser" >
        <b-form-group
          label="Username"
          label-cols-sm="2"
          label-for="username">
          <b-form-input name="username" id="username"
          v-model="user.username" required></b-form-input>
        </b-form-group>
        <b-form-group
          label="Name"
          label-cols-sm="2"
          label-for="name">
          <b-form-input name="name" id="name"
          v-model="user.name" required></b-form-input>
        </b-form-group>
        <b-form-group
          label="Organisation"
          label-cols-sm="2"
          for="organisation">
          <b-form-input name="organisation" id="organisation"
            v-model="user.organisation" required>
          </b-form-input>
        </b-form-group>
        <b-form-group
          label="Email address"
          label-cols-sm="2"
          for="email_address">
          <b-form-input name="email_address" id="email_address"
            v-model="user.email_address" required>
          </b-form-input>
        </b-form-group>
        <template v-if="mode=='edit'">
          <b-form-group
            label-cols-sm="2"
            for="change_password">
            <b-form-checkbox
              name="change_password" id="change_password" v-model="changePassword">
             <b>Change password</b>
            </b-form-checkbox>
          </b-form-group>
        </template>
        <b-form-group
          label="Password"
          for="password"
          label-cols-sm="2">
          <b-form-input type="password" name="password" id="password"
            :disabled="!(changePassword)"
            v-model="user.password"
            v-if="mode=='edit'">
          </b-form-input>
          <b-form-input type="password" name="password" id="password"
            v-model="user.password"
            required
            v-else>
          </b-form-input>
        </b-form-group>
        <h4>Default Permissions</h4>
        <template v-if="loggedInUser.roles_list.includes('admin')">
          <b-form-group
            label="User roles"
            label-cols-sm="2"
            for="user_roles">
            <v-select :options="roles" label="name" value="id" v-model="user.user_roles" multiple
              :reduce="role => role.id" :get-option-label="getRoleLabel" required>
            </v-select>
          </b-form-group>
        </template>
        <b-form-group
          label="View projects"
          label-cols-sm="2"
          for="view">
          <b-select name="view" id="view"
          class="form-control"
          :options="viewOptions"
          v-model="user.view"
          required>
          </b-select>
        </b-form-group>

        <b-form-group
          label="Edit projects"
          label-cols-sm="2"
          for="view">
          <b-select name="edit" id="edit"
          class="form-control"
          :options="editOptions"
          v-model="user.edit"
          required>
          </b-select>
        </b-form-group>
        <b-form-group>
          <b-button type="submit" variant="primary">
            <font-awesome-icon :icon="['fa', 'save']" />
            <span v-if="mode=='edit'">Update User</span>
            <span v-else>Add User</span>
          </b-button>
        </b-form-group>
      </b-form>
      <template v-if="loggedInUser.roles_list.includes('admin') && mode=='edit'">
        <hr />
        <form>
          <h4>Organisations</h4>
          <div class="row">
            <div class="col-md-12">
              <p class="lead">Give this user permissions to view or edit data for a particular organisation.</p>
              <b-table :fields="permissionFields" :items="permissionItems" :busy="isBusy">
                <template v-slot:table-busy>
                  <div class="text-center">
                    <b-spinner class="align-middle" label="Loading..."></b-spinner>
                    <strong>Loading...</strong>
                  </div>
                </template>
                <template v-slot:cell(organisation)="data">
                  <permission-organisation :permission_id="data.item.id"
                  :organisation_id.sync="data.item.organisation_id"
                  :organisations="organisations"
                  :update-changed-permission="updateChangedPermission"></permission-organisation>
                </template>
                <template v-slot:cell(permission)="data">
                  <permission-value :permission_id="data.item.id"
                  :permission_value.sync="data.item.permission_value"
                  :permission-values="permissionValues"
                  :update-changed-permission="updateChangedPermission"></permission-value>
                </template>
                <template v-slot:cell(delete)="data">
                  <a class="btn btn-sm btn-danger"
                   @click.prevent="confirmDeletePermission(data.item.id, data.index)"
                   href="">
                   <font-awesome-icon :icon="['fa', 'trash-alt']" />
                  </a>
                </template>
              </b-table>
            </div>
          </div>
        </form>
        <a class="btn btn-primary addPermission" href=""
          @click.prevent="addPermission">
          <font-awesome-icon :icon="['fa', 'plus']" />
          Add organisation
        </a>
          <hr />
        <b-form-group>
          <b-button type="submit" class="btn btn-danger btn-sm"
            @click.prevent="confirmDeleteUser()">
              <font-awesome-icon :icon="['fa', 'trash-alt']" /> Delete User
          </b-button>
        </b-form-group>
      </template>
    </template>
  </div>
</template>
<script>
import Vue from 'vue'
import PermissionOrganisation from './UserEditor/permission-organisation.vue'
import PermissionValue from './UserEditor/permission-value.vue'
import { mapGetters } from 'vuex'
import config from '~/nuxt.config'
export default {
  components: {
    PermissionOrganisation,
    PermissionValue
  },
  head() {
    return {
      title: this.mode == 'new' ? `New User | ${config.head.title}` : `Edit User | ${config.head.title}`
    }
  },
  data() {
    return {
      permissionFields: ["organisation", "permission", "delete"],
      permissionItems: [],
      changePassword: false,
      isBusy: true,
      permissionValues: [],
      organisations: [],
      alreadyPushed: false,
      roles: [],
      user_id: this.$route.params.id,
      user: {},
      viewOptions: [{
        'value': 'none',
        'text': 'Cannot view'
      },
      {
        'value': 'both',
        'text': 'View all domestic and external projects'
      },
      {
        'value': 'domestic',
        'text': 'View all domestic projects (PSIP / PIU)'
      },
      {
        'value': 'external',
        'text': 'View all external projects (Aid / AMCU)'
      }],
      editOptions: [{
        'value': 'none',
        'text': 'Cannot edit'
      },
      {
        'value': 'both',
        'text': 'Edit all domestic and external projects'
      },
      {
        'value': 'domestic',
        'text': 'Edit all domestic projects (PSIP / PIU)'
      },
      {
        'value': 'external',
        'text': 'Edit all external projects (Aid / AMCU)'
      }]
    }
  },
  mounted: function() {
    this.getUser()
    if (this.mode=='edit') {
      this.getUserPermissions()
    }
  },
  computed: {
    mode() {
      return this.$route.params.id ? 'edit' : 'new'
    },
    getUserURL() {
      if (this.mode=='edit') {
        return `users/${this.user_id}/`
      }
      return `users/new/`
    },
    ...mapGetters(['isAuthenticated', 'loggedInUser'])
  },
  methods: {
    getRoleLabel (role) {
      return `${role.name}`
    },
    getUser() {
      this.$axios
        .get(this.getUserURL)
        .then((response) => {
          this.user = response.data.user
          Vue.set(this.user, 'user_roles', response.data.userRoles)
          this.roles = response.data.roles
        })
        .catch(error => {
          if (error.request.status == 404) {
            this.$router.push({ name: 'users'})
          }
        });
      this.isBusy = false
    },
    updateUser() {
      this.$axios
        .post(this.getUserURL, this.user).then(response => {
            if (this.mode == 'new') {
              this.user = response.data.user
              this.$router.push({ name: 'users-id', params: {id: this.user.id}})
            }
            const msg = this.mode == 'new' ? 'Your user was successfully created! You can continue adding permissions.' : 'Your user was successfully updated.'
            const title = this.mode == 'new' ? 'User created' : 'User updated'
            this.$root.$bvToast.toast(msg, {
              title: title,
              autoHideDelay: 10000,
              solid: true,
              variant: 'success'
            })
          }).catch(response => {
            const created_updated = this.mode == 'new' ? 'created' : updated
            this.$bvToast.toast(`Sorry, something went wrong, and your user could not be ${created_updated}.`, {
              title: "Error.",
              variant: "danger"
            })
          })
    },
    getUserPermissions: function() {
      this.$axios
        .get(`users/${this.user_id}/permissions/`)
        .then((response) => {
          this.permissionItems = response.data.permissions
          this.organisations = response.data.organisations
          this.permissionValues = response.data.permission_values
          Vue.set(this.user, 'user_roles', response.data.user_roles.map(role => {
            return role.role_id
          }))
          this.roles = response.data.roles
        });
    },
    confirmDeleteUser: function(delete_url, username) {
        this.$bvModal.msgBoxConfirm(`Are you sure you want to delete this user (${this.user.username})? This action cannot be undone!`, {
          title: 'Confirm delete',
          okVariant: 'danger',
          okTitle: 'Confirm delete',
          hideHeaderClose: false,
          centered: true
        })
        .then(value => {
          if (value) {
            this.$axios.post(`users/delete/`, {
              username: this.user.username
            })
            .then(result => {
              this.$root.$bvToast.toast(`The user ${this.user.username} was successfully deleted.`, {
                title: title,
                autoHideDelay: 10000,
                solid: true,
                variant: 'success'
              })
              this.$router.push({ name: 'users'})
            })
            .catch(error => {
              this.$bvToast.toast(`Sorry, something went wrong, and this user (${this.user.username}) could not be deleted.`, {
                title: "Error.",
                variant: "danger"
              })
            })
          }
        })
        .catch(err => {
          alert("Sorry, there was an error, and that user couldn't be deleted.")
        })
    },
    confirmDeletePermission: function(permission_id, index) {
        this.$bvModal.msgBoxConfirm('Are you sure you want to delete this permission? This action cannot be undone!', {
          title: 'Confirm delete',
          okVariant: 'danger',
          okTitle: 'Confirm delete',
          hideHeaderClose: false,
          centered: true
        })
          .then(value => {
            if (value) {
              this.deletePermission(permission_id, index)
            }
          })
          .catch(err => {
            alert("Sorry, there was an error, and that permission couldn't be deleted.")
          })
    },
    addPermission: function() {
      var permission_name = "view"
      this.$axios.post(`users/${this.user_id}/permissions/`, {
          "permission_name": "view_edit",
          "permission_value": "view",
          "action": "add"
        })
        .then(returndata => {
          if (returndata == 'False'){
              alert("There was an error updating that permission.");
          } else {
            this.permissionItems.push(returndata.data)
          }
        }).catch(err=> {
          alert("Sorry, there was an error, and a new permission couldn't be added.")
        });
    },
    deletePermission: function(permission_id, index) {
      this.$axios.post(`users/${this.user_id}/permissions/`, {
        "id": permission_id,
        "action": "delete"
      })
        .then(returndata => {
          if (returndata == 'False'){
              alert("There was an error deleting that permission.");
          } else {
            this.$delete(this.permissionItems, index)
          }
        })
    },
    updateChangedPermission: function(_this, permission_id, attr, value) {
     this.$axios.post(`users/${this.user_id}/permissions/`, {
        'id': permission_id,
        'action': 'edit',
        'attr': attr,
        'value': value
      })
      .then(resultdata => {
        _this.validation = true
      }).catch(error => {
        _this.validation = false
      });
    }
  }
}
</script>
