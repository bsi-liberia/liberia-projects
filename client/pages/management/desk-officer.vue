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
      <div id="reportingOrgDataQuality">
        <b-row>
          <b-col>
            <b-breadcrumb :items="breadcrumbItems"></b-breadcrumb>
          </b-col>
        </b-row>
        <b-row>
          <b-col lg="9">
            <h1>Hello,
              <template v-if="user_name">{{ user_name }}</template>
              <template v-else>Desk Officer</template></h1>
            <p class="lead">This is your personalised Desk Officer Dashboard. It shows
              a simple summary of reporting for each of your organisations in the
              Liberia Project Dashboard, and helps you manage data collection.</p>
          </b-col>
          <b-col lg="3" v-if="users.length > 1">
            <b-form-group class="text-right"
            label="Select user:">
              <b-select
                v-model="user_id"
                :options="users"
              >
                <template v-slot:first>
                  <option :value="null">Select a user</option>
                </template>
              </b-select>
            </b-form-group>
          </b-col>
        </b-row>
        <hr />
        <b-row>
          <b-col lg="6">
            <h2>Data collection for {{ selectedQuarter }}</h2>
            <p class="lead">You can use the section below to track progress with your donors.
              For the data request, you can generate <nuxt-link :to="{ name: 'exports'}">
              donor-specific templates from the Exports page</nuxt-link>.</p>
            <b-table class="table" :busy="isBusy" :fields="statusFields" :items="items"
              sort-by="name" show-empty responsive>
              <template #table-busy>
                <div class="text-center">
                  <b-spinner class="align-middle" label="Loading..."></b-spinner>
                  <strong>Loading...</strong>
                </div>
              </template>
              <template #cell(donor)="data">
                <a :href="'/activities/#?reporting_org_id=' + data.item.id"
                  title="View this organisation's projects"
                  v-b-tooltip.hover>
                  {{ data.item.name }}
                </a>
              </template>
              <template #cell(status)="data">
                <b-input-group>
                  <b-input-group-prepend v-if="selectedStatus[data.item.id]" is-text>

                    <span
                      :title="selectedStatusOrganisation[data.item.id].name"
                      :class="selectedStatusOrganisation[data.item.id].colour"
                      v-b-tooltip.hover>
                      <font-awesome-icon :icon="[selectedStatusOrganisation[data.item.id].icon_class, selectedStatusOrganisation[data.item.id].icon]" />
                      <span class="sr-only">selectedStatusOrganisation[data.item.id].name }}</span>
                    </span>
                  </b-input-group-prepend>
                  <b-input-group-prepend v-else is-text>
                    <span
                      title="Unknown"
                      class="text-muted"
                      v-b-tooltip.hover>
                      <font-awesome-icon :icon="['fa', 'question-circle']" />
                      <span class="sr-only">selectedStatusOrganisation[data.item.id].name }}</span>
                    </span>
                  </b-input-group-prepend>
                  <b-select :options="statuses" v-model="selectedStatus[data.item.id]"
                    text-field="name" value-field="id" @change="updateOrganisationResponse(data.item.id)">
                    <template v-slot:first>
                      <option :value="null">Select one...</option>
                    </template>
                  </b-select>
                </b-input-group>
              </template>
            </b-table>
          </b-col>
          <b-col lg="6">
            <b-card variant="info">
              <template #header>
                <h4>Data collection timetable</h4>
              </template>
              <b-table small :fields="dataCollectionFields" :items="dataCollectionCalendar">
                <template #cell(date)="data">
                  <b>
                    {{ data.item.date }}
                  </b>
                </template>
              </b-table>
            </b-card>
          </b-col>
        </b-row>
        <hr />
        <b-row>
          <b-col lg="9">
            <h2>Data quality over time</h2>
              <p class="lead">
                Your data quality dashboard shows:
              </p>
            <ul>
              <li>MTEF projections for the current and previous fiscal year</li>
              <li>Disbursements by quarter for the last four quarters</li>
            </ul></p>
            <p class="lead">
              Data quality is marked by the following symbols:
              <ul>
                <li>
                  <span class="text-success">
                  <font-awesome-icon :icon="['fa', 'check-circle']" />
                    <span class="sr-only">Yes</span>
                  </span>
                  denotes spending recorded (for any project) in the relevant period;
                </li>
                <li>
                  <span class="text-secondary">
                  <font-awesome-icon :icon="['far', 'times-circle']" />
                    <span class="sr-only">No</span>
                  </span>
                  denotes no spending recorded (for any project) in the relevant period.
                </li>
              </ul>
            </p>
          </b-col>
          <b-col lg="3">
            <b-form-group class="text-right"
            label="Display as:">
              <b-form-radio-group
                id="btn-radios-1"
                v-model="selectedDisplayOption"
                :options="displayOptions"
                buttons
                button-variant="outline-dark"
              ></b-form-radio-group>
            </b-form-group>
          </b-col>
        </b-row>
        <b-table id="reportingOrgs" :fields="fields" :items="items"
          :busy="isBusy" sort-by="name" show-empty responsive>
          <template #table-busy>
            <div class="text-center">
              <b-spinner class="align-middle" label="Loading..."></b-spinner>
              <strong>Loading...</strong>
            </div>
          </template>
          <template #thead-top="data">
            <b-tr>
              <b-th>&nbsp;</b-th>
              <b-th variant="light" colspan="3" class="text-center table-forwardspends">MTEF Projections</b-th>
              <b-th colspan="4" class="text-center">Disbursements</b-th>
            </b-tr>
          </template>
          <template #cell(name)="data">
            <nuxt-link :to="{ name: 'activities', query: {reporting_org_id: data.item.id}}"
              title="View this organisation's projects"
              v-b-tooltip.hover>
              {{ data.item.name }}
            </nuxt-link>
          </template>
          <template v-slot:[`cell(forwardspends_${currentprevious}year)`]="data"
            v-for="currentprevious in ['current', 'previous', 'next']">
            <template v-if="selectedDisplayOption == 'check'">
              <span
                :title="data.item.forwardspends[currentprevious].status.name"
                :class="data.item.forwardspends[currentprevious].status.colour"
                v-b-tooltip.hover>
                <font-awesome-icon :icon="[data.item.forwardspends[currentprevious].status.icon_class, data.item.forwardspends[currentprevious].status.icon]" />
                <span class="sr-only">{{ data.item.forwardspends[currentprevious].status.name }}</span>
              </span>
            </template>
            <template v-else>
              {{ numberFormatter(data.item.forwardspends[currentprevious].value) }}
            </template>
          </template>
          <template v-slot:[`cell(${quarter})`]="data" v-for="quarter in quarters">
            <template v-if="selectedDisplayOption == 'check'">
              <span
                :title="data.item.disbursements[quarter].status.name"
                :class="data.item.disbursements[quarter].status.colour"
                v-b-tooltip.hover>
                <font-awesome-icon :icon="[data.item.disbursements[quarter].status.icon_class, data.item.disbursements[quarter].status.icon]" />
                <span class="sr-only">{{ data.item.disbursements[quarter].status.name }}</span>
              </span>
            </template>
            <template v-else>
              {{ numberFormatter(data.item.disbursements[quarter].value) }}
            </template>
          </template>
        </b-table>
      </div>
    </template>
  </div>
</template>
<style>
.table-forwardspends {
    background-color: #eeeeee;
}
</style>
<script>
export default {
  data() {
    return {
      fields: [],
      items: [],
      quarters: [],
      isBusy: true,
      breadcrumbItems: [
        {
          text: 'Management',
          to: { name: 'management' }
        },
        {
          text: 'Desk Officer Dashboard',
          active: true
        }
      ],
      displayOptions: [
        {
          'text': 'Checklist',
          'value': 'check'
        },
        {
          'text': 'Value',
          'value': 'value'
        }
      ],
      selectedDisplayOption: "check",
      users: [],
      user_id: null,
      user_name: null,
      availableQuarters: [],
      selectedQuarter: null,
      statusFields: ['donor', 'status'],
      statuses: [],
      selectedStatus: {},
      dataCollectionCalendar: [],
      dataCollectionFields: [
        {
          "key": "date",
          "thStyle": {"min-width":"120px"}
        },
        {
          "key": "data_request"
        }]
    }
  },
  head() {
    return {
      title: `Data quality dashboard | ${this.$config.title}`
    }
  },
  mounted: function() {
    this.getDataQualityData()
  },
  computed: {
    selectedStatusOrganisation() {
      var statusObj = this.statuses.reduce(
      (obj, item) => {
        obj[item.id] = item
        return obj
      }, {})
      return Object.entries(this.selectedStatus).reduce(
        (obj, item) => {
          obj[item[0]] = statusObj[item[1]]
          return obj
        },
      {})
    }
  },
  watch: {
    user_id: function() {
      this.getDataQualityData()
    }
  },
  methods: {
    updateOrganisationResponse(organisation_id){
      var status_id = this.selectedStatus[organisation_id]
      this.postOrganisationResponse(organisation_id, status_id)
    },
    numberFormatter(value) {
      if (value == null) { return 0.00 }
      return "$" + value.toLocaleString(undefined, {minimumFractionDigits: 0})
    },
    makeFields: function (data) {
      var _fields = [{
            key: 'name',
            sortable: true
          },
          {
            key: 'forwardspends_previousyear',
            label: data.previous_year,
            class: "number table-forwardspends",
            variant: "light"
          },
          {
            key: 'forwardspends_currentyear',
            label: data.current_year,
            class: "number table-forwardspends",
            variant: "light"
          },
          {
            key: 'forwardspends_nextyear',
            label: data.next_year,
            class: "number table-forwardspends",
            variant: "light"
          }]
      return Object.entries(data.list_of_quarters).reduce(
            (obj, item) => {
              obj.push({
                key: item[0],
                label: item[1],
                class: "number"
              })
              this.quarters.push(item[0])
              return obj
            },
            _fields)
    },
    postOrganisationResponse: function(organisation_id, response_id) {
      if (this.user_id != null) {
        var user_id_string = `?user_id=${this.user_id}`
      } else { var user_id_string = '' }
      this.$axios
        .post(`management/reporting_orgs_user.json${user_id_string}`, {
            organisation_id: organisation_id,
            response_id: response_id,
            fyfq: this.selectedQuarter
          }).then(response => {
            console.log(response)
          })
    },
    makeDonorStatus: function(item) {
      if (item.responses_fys[this.selectedQuarter]) {
        return item.responses_fys[this.selectedQuarter]
      } else if (item.disbursements[this.availableQuarters[this.selectedQuarter]]) {
        if (item.disbursements[this.availableQuarters[this.selectedQuarter]].status.id == undefined) { return null }
        return item.disbursements[this.availableQuarters[this.selectedQuarter]].status.id
      } else {
        return null
      }
    },
    getDataQualityData: function() {
      if (this.user_id != null) {
        var user_id_string = `?user_id=${this.user_id}`
      } else { var user_id_string = '' }
      this.$axios
        .get(`management/reporting_orgs_user.json${user_id_string}`)
        .then((response) => {
          this.fields = this.makeFields(response.data)
          this.statuses = response.data.statuses
          this.items = response.data.orgs
          this.availableQuarters = Object.entries(response.data.list_of_quarters).reduce((obj, qtr) => {
            obj[qtr[1]] = qtr[0]
            return obj
          }, {})
          this.selectedQuarter = Object.values(
            response.data.list_of_quarters).slice(-1).pop()
          this.selectedStatus = response.data.orgs.reduce(
            (obj, item) => {
              obj[item.id] = this.makeDonorStatus(item)
              return obj
            },
            {})
          this.users = response.data.users
          this.user_name = response.data.user_name
          this.user_id = response.data.user_id
          this.isBusy = false
          this.dataCollectionCalendar = response.data.data_collection_calendar
        });
    }
  }
}
</script>
