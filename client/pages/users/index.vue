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
      <div class="row">
        <div class="col-md-10">
          <h1>Users</h1>
        </div>
        <div class="col-md-2 text-right">
          <nuxt-link class="btn btn-success btn-large" :to="{ name: 'users-new'}">
            <font-awesome-icon :icon="['fa', 'plus']" />
            New user
          </nuxt-link>
        </div>
      </div>
      <div class="alert alert-secondary" role="alert">View the
        <nuxt-link :to="{ name: 'users-log'}">
          Activity log
        </nuxt-link>
      </div>
      <b-table class="table" :fields="fields" :items="items" :busy="isBusy">
        <template v-slot:table-busy class="text-center">
          <b-spinner class="align-middle" label="Loading..."></b-spinner>
          <strong>Loading...</strong>
        </template>
        <template v-slot:cell(user_roles)="data">
          <b-badge variant="secondary" v-for="role in data.item.user_roles" v-bind:key="role.id">
            {{ role.name }}
          </b-badge>
        </template>
        <template v-slot:cell(edit)="data">
          <nuxt-link :to="{ name: 'users-id', params: {id: data.item.id}}"
            title="Edit user"
            v-b-tooltip.hover>
            <font-awesome-icon :icon="['fa', 'edit']" />
          </nuxt-link>
        </template>
      </b-table>
    </template>
  </div>
</template>
<script>
export default {
  data() {
    return {
      fields: [],
      items: [],
      isBusy: true
    }
  },
  head() {
    return {
      title: `Users | ${this.$config.title}`
    }
  },
  mounted: function() {
    this.getUsers()
  },
  methods: {
    getUsers: function() {
      this.$axios
        .get(`users.json`)
        .then((response) => {
          this.fields = ['username', 'name', 'organisation', 'user_roles', 'edit'].map(field => {
            return { 'key': field, 'sortable': true }
          })
          this.items = response.data.users
          this.isBusy = false
        });
      }
  }
}
</script>
