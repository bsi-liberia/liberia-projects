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
      <h1>Activity Log</h1>
      <b-form-group
          label-cols-sm="2"
          label-cols-lg="2"
          label-class="font-weight-bold"
          description="Optionally select a user to filter the activity log."
          label="Select a user"
          label-for="select-user">
        <b-form-select
          id="select-user"
          v-model="selectedUser"
          :options="users"
          value-field="id"
          text-field="username"
          >
          <template v-slot:first>
            <option :value="null">Filter by user</option>
          </template>
        </b-form-select>
      </b-form-group>
      <b-table id="usersLog" :fields="fields" :items="items" :busy="isBusy" show-empty responsive>
        <template v-slot:table-busy>
          <div class="text-center">
            <b-spinner class="align-middle" label="Loading..."></b-spinner>
            <strong>Loading...</strong>
          </div>
        </template>
        <template v-slot:cell(user)="data">
          <a :href="data.item.user.url">
            {{ data.item.user.username }}</a>
        </template>
        <template v-slot:cell(action)="data">
            {{ data.item.mode.text }} {{ data.item.target.text }}
        </template>
        <template v-slot:cell(activity)="data">
          <nuxt-link :to="{ name: 'activities-id', params: {id: data.item.activity.id }}">
            {{ data.item.activity.title }}
          </nuxt-link>
        </template>
        <template v-slot:cell(details)="data">
          <a href="#" :data-id="data.item.id"
          v-on:click.prevent="getDetails">Details</a>
        </template>
      </b-table>
      <b-pagination
        v-model="currentPage"
        :total-rows="rows"
        :per-page="perPage"
        aria-controls="usersLog"
        :disabled="rows < perPage"
      ></b-pagination>
      <b-modal id="activityLogDetail" size="lg" scrollable ok-only>
        <template v-slot:modal-title>
          Activity:
          <nuxt-link :to="{ name: 'activities-id', params: {id: activitylog_detail.activity.id }}">
            {{ activitylog_detail.activity.title }}
          </nuxt-link>
        </template>
        {{ activitylog_detail.user.username }} {{ activitylog_detail.mode.text }}
        {{ activitylog_detail.target.text }} ({{ activitylog_detail.target.id }})
        <hr />
        <template v-if="activitylog_detail.old_value">
          <p><b>Previous value</b></p>
          <pre v-html="prettyAreaData(activitylog_detail.old_value)"></pre>
        </template>
        <template v-if="activitylog_detail.value">
          <p><b>New value</b></p>
          <pre v-html="prettyAreaData(activitylog_detail.value)"></pre>
        </template>
        <template v-if="activitylog_detail.target.obj">
          <p><b>{{ activitylog_detail.target.obj_title }} detail</b></p>
          <pre v-html="prettyAreaData(activitylog_detail.target.obj)"></pre>
        </template>
      </b-modal>
    </template>
  </div>
</template>
<script>
export default {
  data() {
    return {
      rows: 0,
      perPage: 10,
      currentPage: 1,
      fields: ['activity', 'action', 'user', 'date', 'details'],
      items: [],
      activitylog_detail: {
        activity: { title: "", id: "" },
        user: { username: "" },
        mode: { text: "" },
        target: { text: ""}, value: ""
      },
      selectedUser: null,
      users: [],
      isBusy: true
    }
  },
  middleware: 'auth',
  created: function() {
    this.getUsersWithEditPermissions()
    this.getActivityLog(1)
  },
  watch: {
    currentPage: function(newPage) {
      this.getActivityLog(newPage)
    },
    selectedUser: function(newUser) {
      this.getActivityLog(this.currentPage)
    }
  },
  methods: {
    getUsersWithEditPermissions: function() {
      this.$axios
        .get('users.json')
        .then((response) => {
          this.users = response.data.users;
        });
    },
    getActivityLog: function(currentPage) {
      this.$axios
        .get('activitylog.json',
          { params: {
              page: currentPage,
              user_id: this.selectedUser
            }
          })
        .then((response) => {
          this.items = response.data.items;
          this.rows = response.data.count;
          this.isBusy = false
        });
    },
    getDetails: function(e) {
      var activitylog_id = e.target.dataset.id;
      this.$axios
        .get(`activitylog/${activitylog_id}.json`)
        .then(response => {
          this.activitylog_detail = response.data.data;
          this.$bvModal.show("activityLogDetail")
        });
    },
    prettyAreaData: function(data) {
      if (data == undefined) { return "" }
      var json = JSON.stringify(data, null, 2)
      json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      return json.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+]?\d+)?)/g, function(match) {
        var cls = 'number'
        if (/^"/.test(match)) {
          if (/:$/.test(match)) {
            cls = 'key'
          } else {
            cls = 'string'
          }
        } else if (/true|false/.test(match)) {
          cls = 'boolean'
        } else if (/null/.test(match)) {
          cls = 'null'
        }
        return '<span class="' + cls + '">' + match + '</span>'
      })
    }
  }
}
</script>
