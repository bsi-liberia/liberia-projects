
var api_user_permissions = "permissions/"
Vue.config.devtools = true
Vue.component('permission-organisation', {
  data() {
    return { validation: null }
  },
  props: ["permission_id", "organisation_id", "organisations", "updateChangedPermission"],
  template: `
          <b-form-group :state="validation">
            <b-select name="organisation_id" id="organisation_id"
            class="form-control" :options="organisations"
            text-field="name" value-field="id" v-model="organisation_id"
            :state="validation">
            </b-select>
          </b-form-group>`,
  watch: {
    organisation_id: {
      handler: function(newValue) {
        this.updateChangedPermission(this, this.permission_id, 'organisation_id', newValue)
      }
    }
  }
})
Vue.component('permission-value', {
  data() {
    return {
      validation: null
    }
  },
  props: ["permission_id", "permission_value", "permissionValues", "updateChangedPermission"],
  template: `
          <b-form-group state="validation">
            <b-select name="permission_value" id="permission_value"
            class="form-control" :options="permissionValues"
            text-field="name" v-model="permission_value"
            :state="validation">
            </b-select>
          </b-form-group>`,
  watch: {
    'permission_value': {
      handler: function(newValue) {
        this.updateChangedPermission(this, this.permission_id, 'permission_value', newValue)
      }
    }
  }
})
new Vue({
  el: "#app",
  delimiters: ["[[", "]]"],
  data() {
    return {
      permissionFields: ["organisation", "permission", "delete"],
      permissionItems: [],
      changePassword: false,
      isBusy: true,
      permissionValues: [],
      organisations: []
    }
  },
  mounted: function() {
    this.getUserPermissions()
  },
  methods: {
    getUserPermissions: function() {
      axios
        .get(`${api_user_permissions}`)
        .then((response) => {
          this.permissionItems = response.data.permissions
          this.isBusy = false
          this.organisations = response.data.organisations
          this.permissionValues = response.data.permission_values
        });
    },
    confirmDeleteUser: function(delete_url, username) {
        this.$bvModal.msgBoxConfirm('Are you sure you want to delete this user? This action cannot be undone!', {
          title: 'Confirm delete',
          okVariant: 'danger',
          okTitle: 'Confirm delete',
          hideHeaderClose: false,
          centered: true
        })
          .then(value => {
            if (value) {
              axios.post(delete_url, {
                username: username
              })
              .then(result => {
                location.reload()
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
      axios.post(api_user_permissions, {
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
      axios.post(api_user_permissions, {
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
      axios.post(api_user_permissions, {
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
})
