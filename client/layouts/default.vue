<template>
  <div>
    <b-navbar toggleable="lg" type="light" variant="light" sticky>
      <b-container>
        <b-navbar-brand :to="'/'">
          <img src="~/assets/img/flag-lr.png" alt="Flag" />
          Liberia Project Dashboard
        </b-navbar-brand>
        <b-navbar-toggle target="navbar-collapse"></b-navbar-toggle>
        <b-collapse id="navbar-collapse" is-nav>
          <b-navbar-nav v-if="isAuthenticated">
            <b-nav-item :to="{name: 'index'}" exact-active-class="active">Home
            </b-nav-item>
            <b-nav-item  :to="{name: 'activities'}" active-class="active">Activities</b-nav-item>
            <template v-if="['domestic', 'external', 'both'].includes(loggedInUser.permissions_dict.view)">
              <b-nav-item-dropdown text="Reports" v-if="['domestic', 'external', 'both'].includes(loggedInUser.permissions_dict.view)">
                <template v-if="['domestic', 'both'].includes(loggedInUser.permissions_dict.edit) || loggedInUser.roles_list.includes('management') || loggedInUser.roles_list.includes('admin')">
                  <b-dropdown-item :to="{name: 'reports-milestones'}" active-class="active">PSIP Project Development and Appraisal Tracking</b-dropdown-item>
                  <b-dropdown-item :to="{name: 'reports-psip_disbursements'}" active-class="active">PSIP Disbursements</b-dropdown-item>
                </template>
                <template v-if="['external', 'both'].includes(loggedInUser.permissions_dict.view)">
                  <b-dropdown-item :to="{name: 'reports-aid_disbursements'}" active-class="active">Aid Disbursements</b-dropdown-item>
                  <b-dropdown-item :to="{name: 'reports-results'}" active-class="active">Results</b-dropdown-item>
                </template>
                <b-dropdown-item :to="{name: 'reports-counterpart_funding'}" active-class="active">Counterpart funding</b-dropdown-item>
              </b-nav-item-dropdown>
            </template>
          </b-navbar-nav>
          <!-- Right aligned nav items -->
          <b-navbar-nav class="ml-auto">
            <template v-if="isAuthenticated">
              <b-nav-item :to="{name: 'results'}" v-if="loggedInUser.roles_list.includes('results-data-entry') || loggedInUser.roles_list.includes('results-data-design')">Results</b-nav-item>
              <b-nav-item :to="{name: 'management-desk-officer'}" v-if="loggedInUser.roles_list.includes('desk-officer')">Management</b-nav-item>
              <b-nav-item :to="{name: 'management'}" v-if="loggedInUser.roles_list.includes('management') || loggedInUser.roles_list.includes('admin')">Management</b-nav-item>
              <template v-if="['domestic', 'external', 'both'].includes(loggedInUser.permissions_dict.view)">
                <b-nav-item :to="{name: 'export'}">Export data</b-nav-item>
                <b-nav-item :to="{name: 'help'}" active-class="active">Help</b-nav-item>
              </template>
            </template>
            <b-nav-item-dropdown right v-if="isAuthenticated">
              <!-- Using 'button-content' slot -->
              <template v-slot:button-content>
                <em>Logged in as {{ loggedInUser.username }}</em>
              </template>
              <template v-if="loggedInUser.administrator">
              <b-dropdown-item :to="{name: 'codelists'}" active-class="active">Manage codelists</b-dropdown-item>
              <b-dropdown-item :to="{name: 'users'}" active-class="active">Users</b-dropdown-item>
              </template>
              <b-dropdown-item href="#" @click="logout">Sign Out</b-dropdown-item>
            </b-nav-item-dropdown>
            <b-nav-item to="/login" right v-else>Sign In</b-nav-item>
          </b-navbar-nav>
        </b-collapse><!--/.nav-collapse -->
      </b-container>
    </b-navbar>
    <b-container :style="pageMargins" :fluid="$route.name=='index'">
      <nuxt />
    </b-container>
    <footer class="footer">
      <hr />
      <b-container>
        <b-row>
          <b-col>
            <p><a href="https://github.com/bsi-liberia/liberia-projects">Source code on Github</a>, released under the <a href="http://www.gnu.org/licenses/agpl-3.0.html">AGPL v3.0 License</a>.</p>
          </b-col>
          <b-col class="text-right">
              <p><a href="http://twitter.com/mark_brough">@mark_brough</a></p>
          </b-col>
      </b-row>
      </b-container>
    </footer>
  </div>
</template>

<style>
.number {
  text-align: right;
}
.navbar-brand {
  height: 50px;
  color:#333333;
  max-height: 50px;
  overflow: visible;
  padding-top: 10px;
  padding-bottom: 0;
}
.navbar-default, nav.navbar {
    background: #fefefe;
    background: -moz-linear-gradient(180deg,#ffffff 0%,#eeeeee 100%);
    background: -webkit-gradient(linear,left bottom,right top,color-stop(0%,#ffffff),color-stop(100%,#eeeeee));
    background: -webkit-linear-gradient(45deg,#ffffff 0%,#eeeeee 100%);
    background: -o-linear-gradient(45deg,#ffffff 0%,#eeeeee 100%);
    background: -ms-linear-gradient(45deg,#ffffff 0%,#eeeeee 100%);
    background: linear-gradient(180deg, #ffffff 0%, #eeeeee 100%) repeat scroll 0 0 transparent;
    filter: progid:DXImageTransform.Microsoft.gradient(startColorstr='#ffffff',endColorstr='#eeeeee',GradientType=1);
    border-bottom:1px solid #cccccc;

}
</style>
<script>
import { mapGetters } from 'vuex'
import config from '../nuxt.config'

export default {
  data() {
    return {
      title: config.head.title,
      description: config.description
    }
  },
  computed: {
    pageMargins() {
      if (this.$route.name == 'index') {
        return 'padding-left: 0px; padding-right: 0px; margin-bottom: 30px;'
      }
      return 'margin-top: 20px; margin-bottom: 30px;';
    },
    ...mapGetters(['isAuthenticated', 'loggedInUser'])
  },
  methods: {
    async logout() {
      await this.$auth.logout()
        .then(() => {
          this.$router.push('/')
        });
      this.$bvToast.toast('Logged out!', {
        title: `You successfully logged out.`,
        variant: 'success',
        solid: true
      })
    }
  }
}
</script>
