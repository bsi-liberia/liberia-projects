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
            <h1>Data quality</h1>
            <p class="lead">This page shows a simple summary of reporting by
            organisation in the Liberia Project Dashboard. It shows:
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
          <template v-slot:table-busy>
            <div class="text-center">
              <b-spinner class="align-middle" label="Loading..."></b-spinner>
              <strong>Loading...</strong>
            </div>
          </template>
          <template slot:thead-top slot-scope="data">
            <b-tr>
              <b-th>&nbsp;</b-th>
              <b-th variant="light" colspan="3" class="text-center">MTEF Projections</b-th>
              <b-th colspan="4" class="text-center">Disbursements</b-th>
            </b-tr>
          </template>
          <template v-slot:cell(name)="data">
            <nuxt-link :to="{ name: 'activities', query: {reporting_org_id: data.item.id}}"
              title="View this organisation's projects"
              v-b-tooltip.hover>
              {{ data.item.name }}
            </nuxt-link>
          </template>
          <template v-slot:[`cell(forwardspends_${currentprevious}year)`]="data" v-for="currentprevious in ['current', 'previous', 'next']">
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
          href: '/management/'
        },
        {
          text: 'Data Quality',
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
      selectedDisplayOption: "check"
    }
  },
  mounted: function() {
    this.getDataQualityData()
  },
  methods: {
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
            class: "number",
            variant: "light"
          },
          {
            key: 'forwardspends_currentyear',
            label: data.current_year,
            class: "number",
            variant: "light"
          },
          {
            key: 'forwardspends_nextyear',
            label: data.next_year,
            class: "number",
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
    getDataQualityData: function() {
      this.$axios
        .get(`reporting_orgs.json`)
        .then((response) => {
          this.fields = this.makeFields(response.data)
          this.items = response.data.orgs
          this.isBusy = false
        });
    }
  }
}
</script>
