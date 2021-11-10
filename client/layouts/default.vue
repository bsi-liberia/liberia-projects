<template>
  <div>
    <b-navbar toggleable="lg" type="dark" variant="light" sticky>
      <b-container fluid>
        <b-navbar-brand :to="'/'">
          <img src="~/assets/img/flag-lr.png" alt="Flag" />
          {{ this.$config.title }}
        </b-navbar-brand>
        <b-navbar-toggle target="navbar-collapse"></b-navbar-toggle>
        <b-collapse id="navbar-collapse" is-nav>
          <b-navbar-nav>
            <b-nav-item :to="{name: 'index'}" exact-active-class="active">Home
            </b-nav-item>
            <b-nav-item  :to="{name: 'activities'}" active-class="active" v-if="loggedInUser.new_permissions_list.includes('activities')">Activities</b-nav-item>
            <template v-if="isAuthenticated">
              <b-nav-item-dropdown text="Sectors" active-class="active" :class="this.$route.name=='sectors-id' ?'active' : ''">
                <b-dropdown-item :to="{name: 'sectors-id', params: { id: sector.code }}" v-for="sector in sectors" :key="sector.code" active-class="active">
                  {{ sector.name }}
                </b-dropdown-item>
              </b-nav-item-dropdown>
              <b-nav-item-dropdown text="Donors" active-class="active" :class="this.$route.name=='donors-id' ?'active' : ''">
                <div class="scrollable-menu">
                  <b-dropdown-item :to="{name: 'donors-id', params: { id: donor.id }}" v-for="donor in donors" :key="donor.id" active-class="active">
                    {{ donor.name }}
                  </b-dropdown-item>
                </div>
              </b-nav-item-dropdown>
            </template>
            <template v-if="loggedInUser.new_permissions_list.includes('reports')">
              <b-nav-item-dropdown text="Reports">
                <b-dropdown-item :to="{name: 'reports-milestones'}" active-class="active"
                  v-if="loggedInUser.new_permissions_list.includes('reports-milestones')">PSIP Project Development and Appraisal Tracking</b-dropdown-item>
                <b-dropdown-item :to="{name: 'reports-psip_disbursements'}" active-class="active"
                  v-if="loggedInUser.new_permissions_list.includes('reports-psip_disbursements')">PSIP Disbursements</b-dropdown-item>
                <b-dropdown-item :to="{name: 'reports-aid_disbursements'}" active-class="active"
                  v-if="loggedInUser.new_permissions_list.includes('reports-aid_disbursements')">Aid Disbursements</b-dropdown-item>
                <b-dropdown-item :to="{name: 'reports-results'}" active-class="active"
                  v-if="loggedInUser.new_permissions_list.includes('reports-results')">Results</b-dropdown-item>
                <b-dropdown-item :to="{name: 'reports-counterpart_funding'}" active-class="active"
                  v-if="loggedInUser.new_permissions_list.includes('reports-counterpart-funding')">Counterpart funding</b-dropdown-item>
              </b-nav-item-dropdown>
            </template>
          </b-navbar-nav>
          <!-- Right aligned nav items -->
          <b-navbar-nav class="ml-auto">
            <template>
              <b-nav-item :to="{name: 'results'}" v-if="loggedInUser.new_permissions_list.includes('results')">Results</b-nav-item>
              <b-nav-item :to="{name: 'management-desk-officer'}" v-if="loggedInUser.roles_list.includes('desk-officer')">Management</b-nav-item>
              <b-nav-item :to="{name: 'management'}" v-if="loggedInUser.roles_list.includes('management') || loggedInUser.roles_list.includes('admin')">Management</b-nav-item>
              <b-nav-item :to="{name: 'export'}" active-class="active" v-if="loggedInUser.new_permissions_list.includes('export')">Export data</b-nav-item>
              <b-nav-item :to="{name: 'help'}" active-class="active" v-if="loggedInUser.new_permissions_list.includes('help')">Help</b-nav-item>
              <b-nav-item :to="{name: 'about'}" active-class="active" v-if="loggedInUser.new_permissions_list.includes('about')">About</b-nav-item>
            </template>
            <b-nav-item-dropdown right v-if="isAuthenticated">
              <!-- Using 'button-content' slot -->
              <template v-slot:button-content>
                <em>Logged in as {{ loggedInUser.username }}</em>
              </template>
              <template v-if="loggedInUser.administrator">
              <b-dropdown-item :to="{name: 'admin-codelists'}" active-class="active">Manage codelists</b-dropdown-item>
              <b-dropdown-item :to="{name: 'admin-fiscal-years'}" active-class="active">Manage fiscal years</b-dropdown-item>
              <b-dropdown-item :to="{name: 'users'}" active-class="active">Users</b-dropdown-item>
              </template>
              <template v-if="loggedInUser.administrator || loggedInUser.new_permissions_list.includes('world-bank') ">
                <b-dropdown-item :to="{name: 'admin-world-bank'}" active-class="active">Manage World Bank data</b-dropdown-item>
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
@media (min-width: 768px) {
  .scrollable-menu {
      height: auto;
      max-height: calc(100vh - 80px);
      overflow-x: hidden;
  }
}

@media (max-width: 767px) {
  .scrollable-menu {
    height: auto;
    max-height: calc(100vh - 260px);
    overflow-x: hidden;
  }
}
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
    background: #55a44f;
    background: -moz-linear-gradient(45deg,#55a44f 0%,#68b761 100%);
    background: -webkit-gradient(linear,left bottom,right top,color-stop(0%,#55a44f),color-stop(100%,#68b761));
    background: -webkit-linear-gradient(45deg,#55a44f 0%,#68b761 100%);
    background: -o-linear-gradient(45deg,#55a44f 0%,#68b761 100%);
    background: -ms-linear-gradient(45deg,#55a44f 0%,#68b761 100%);
    background: linear-gradient(45deg, #55a44f 0%, #68b761 100%) repeat scroll 0 0 transparent;
    filter: progid:DXImageTransform.Microsoft.gradient(startColorstr='#55a44f',endColorstr='#68b761',GradientType=1);
    border-bottom:1px solid #666666;

}
</style>
<script>
import { mapGetters, mapState } from 'vuex'
import config from '../nuxt.config'

export default {
  data() {
    return {
      title: config.head.title,
      description: config.description,
    }
  },
  computed: {
    pageMargins() {
      if (this.$route.name == 'index') {
        return 'padding-left: 0px; padding-right: 0px; margin-bottom: 30px;'
      }
      return 'margin-top: 20px; margin-bottom: 30px;';
    },
    ...mapGetters(['isAuthenticated', 'loggedInUser']),
    ...mapState(['sectors', 'donors'])
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
