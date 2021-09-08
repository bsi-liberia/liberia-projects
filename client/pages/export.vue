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
      <b-row>
        <b-col md="6">
          <h1>Export data in Excel format</h1>
          <template v-if="['external', 'both'].includes(loggedInUser.permissions_dict.view)">
            <p class="lead">Download all data according to the AMCU Excel export format.</p>
            <p>
              <DownloadFile
                label="Download Excel"
                file-name="activities_external.xlsx"
                variant="primary"
                size="sm"
                url="exports/activities_external.xlsx" />
            </p>
          </template>
          <template v-if="['domestic', 'both'].includes(loggedInUser.permissions_dict.view)">
            <p class="lead">Download all data according to the PIU Excel export format.</p>
            <p>
              <DownloadFile
                label="Download Excel"
                file-name="activities_domestic.xlsx"
                variant="primary"
                size="sm"
                url="exports/activities_domestic.xlsx" />
            </p>
          </template>
        </b-col>
        <template v-if="['external', 'both'].includes(loggedInUser.permissions_dict.view)">
          <b-col md="6">
            <b-alert show variant="light">
              <h3>Advanced download formats</h3>
              <template v-if="['external', 'both'].includes(loggedInUser.permissions_dict.view)">
                <p class="lead">Download detailed AMCU financial transactions data for analysis.</p>
                <p>
                  <DownloadFile
                    label="Download Excel"
                    file-name="activities_external_transactions.xlsx"
                    variant="secondary"
                    size="sm"
                    url="exports/activities_external_transactions.xlsx" />
                </p>
              </template>
              <template v-if="['both'].includes(loggedInUser.permissions_dict.view)">
                <p class="lead">Download integrated dataset of AMCU and PSIP projects.</p>
                <p>
                  <DownloadFile
                    label="Download Excel"
                    file-name="activities_all.xlsx"
                    variant="secondary"
                    size="sm"
                    url="exports/activities_all.xlsx" />
                </p>
              </template>
            </b-alert>
          </b-col>
        </template>
      </b-row>
      <template v-if="loggedInUser.roles_list.includes('desk-officer') || loggedInUser.roles_list.includes('admin') || loggedInUser.roles_list.includes('management')">
        <b-row>
          <b-col md="6">
            <h2>Project Briefs</h2>
            <p class="lead">Download all project briefs for a particular donor.</p>
            <b-form-group label="Select donor"
              label-class="font-weight-bold">
              <b-form-select :options="reportingOrganisations"
              value-field="id"
              text-field="name"
              v-model="projectBriefDonorID">
                <template v-slot:first>
                  <option :value="null">Select a donor</option>
                </template>
              </b-form-select>
            </b-form-group>
            <p v-if="projectBriefDonorID!=null">
              <DownloadFile
                :label="`Download Project Briefs for ${projectBriefDonorName}`"
                :file-name="`Project Briefs ${projectBriefDonorName}.zip`"
                variant="secondary"
                size="sm"
                :url="`project-brief/donor/${projectBriefDonorID}.zip`" />
            </p>
          </b-col>
        </b-row>
      </template>
      <hr />
      <template v-if="loggedInUser.roles_list.includes('desk-officer') || loggedInUser.roles_list.includes('admin')">
        <h1 id="excel-reporting-templates">Excel reporting templates</h1>
        <p class="lead">You can import data that donors have entered on
          AMCU reporting templates. This means you do not have to go through
          each project and manually update it: the templates are automatically
          generated and then you can import one file for each donor.</p>
        <b-row>
          <b-col>
            <b-card>
              <template v-slot:header>
                <h4><font-awesome-icon :icon="['fa', 'download']" /> Download template</h4>
              </template>
              <p>Download a template. Then, send it to the donor, as an email attachment.</p>
              <b-form-group label="Select template type"
                :description="'Selected template: ' + selectedTemplateOptionDescription"
                label-class="font-weight-bold">
                <b-form-radio-group name="template_type" :options="templateOptions"
                  v-model="selectedTemplateOption" stacked></b-form-radio-group>
              </b-form-group>
              <b-form-group label="Select quarter"
                hidden
                label-class="font-weight-bold"
                v-if="selectedTemplateOption=='disbursements'">
                <b-form-select :options="quarters"
                v-model="selectedQuarter">
                </b-form-select>
              </b-form-group>
              <b-form-group label="Select donor"
                description="Generate a reporting template for one or all donors."
                label-class="font-weight-bold">
                <b-form-select :options="reportingOrganisations"
                value-field="id"
                text-field="name"
                v-model="selectedReportingOrganisation">
                  <template v-slot:first>
                    <option value="all">All donors</option>
                  </template>
                </b-form-select>
              </b-form-group>
              <b-form-group label="Select currency"
                description="Select the currency to generate the template in. For example, the donor's own currency."
                label-class="font-weight-bold">
                <b-form-select :options="currencies"
                value-field="code"
                text-field="display_name"
                v-model="selectedCurrency">
                </b-form-select>
              </b-form-group>
              <b-form-group>
                <b-button variant="outline-secondary" v-b-modal.customise-fields><font-awesome-icon :icon="['fa', 'cog']" /> Customise columns</b-button>
              </b-form-group>
              <b-form-group>
                <DownloadFile
                  label="Download template"
                  :file-name="templateDownloadFilename"
                  variant="secondary"
                  :url="templateDownloadURL" />
              </b-form-group>
            </b-card>
          </b-col>
          <b-col>
            <b-card>
              <template v-slot:header>
                <h4><font-awesome-icon :icon="['fa', 'upload']" /> Import template</h4>
              </template>
              <p>Import data you have received back from a donor according to the AMCU import format.</p>
              <b-form @submit.stop.prevent="submitFile(importTemplate, 'exports/import/', 'importMessagesTemplate')">
                <b-form-group label="Select template type"
                  :description="'Selected template: ' + selectedTemplateOptionImportDescription"
                  label-class="font-weight-bold">
                  <b-form-radio-group
                    v-model="importTemplate.template_type"
                    :options="templateOptionsImport"
                    stacked
                    required></b-form-radio-group>
                </b-form-group>
                <b-form-group label="Template file"
                  label-for="file-amcu"
                  label-class="font-weight-bold"
                  description="Select a file to import. The file must be formatted according to the selected template.">
                  <b-form-file id="file-amcu"
                  v-model="importTemplate.file"
                  name="file"
                  required></b-form-file>
                </b-form-group>
                <b-form-group>
                  <b-btn type="submit" :variant="importTemplate.isBusy ? 'secondary' : 'primary'">
                    <template v-if="importTemplate.isBusy">
                      <b-spinner label="Uploading..." small></b-spinner>
                    </template>
                    <template v-else>
                      <font-awesome-icon :icon="['fa', 'upload']" />
                    </template>
                    Import template</b-btn>
                </b-form-group>
                <b-alert variant="success" v-for="(message, id) in importMessagesTemplate" v-bind:key="message" show dismissible>{{ message }}</b-alert>
              </b-form>
            </b-card>
          </b-col>
        </b-row>
        <hr />
      </template>
      <template v-if="loggedInUser.roles_list.includes('piu-desk-officer') || loggedInUser.roles_list.includes('admin')">
        <b-card>
          <template v-slot:header>
            <h3><font-awesome-icon :icon="['fa', 'upload']" /> Upload data for PSIP projects from IFMIS</h3>
          </template>
          <p class="lead">Upload an Excel file containing data on PSIP projects exported from IFMIS.</p>
          <b-form
            @submit.stop.prevent="submitFile(importPSIP, 'exports/import_psip/', 'importMessagesPSIP')">
            <b-form-group label="Select IFMIS data file"
              description="Select an Excel file to import. The file must
                be formatted according to the IFMIS Excel import template."
              label-class="font-weight-bold">
              <b-file id="file" name="file"
                v-model="importPSIP.file"
                required
              ></b-file>
            </b-form-group>
            <b-form-group label="Select Fiscal Year"
              description="Import data for one or all fiscal years."
              label-class="font-weight-bold">
              <b-form-select :options="fys"
              v-model="importPSIP.fiscal_year" name="fiscal_year" required>
                <template v-slot:first>
                  <option value="">All Fiscal Years</option>
                </template>
              </b-form-select>
            </b-form-group>
            <b-form-group>
              <b-btn type="submit" :variant="importPSIP.isBusy ? 'secondary' : 'primary'">
                <template v-if="importPSIP.isBusy">
                  <b-spinner label="Uploading..." small></b-spinner>
                </template>
                <template v-else>
                  <font-awesome-icon :icon="['fa', 'upload']" />
                </template>
                Import data from IFMIS
              </b-btn>
            </b-form-group>
            <b-alert variant="success" v-for="(message, id) in importMessagesPSIP" v-bind:key="message" show dismissible>{{ message }}</b-alert>
          </b-form>
        </b-card>
        <hr />
      </template>
      <h1>Other formats</h1>
      <dl class="dl-horizontal">
        <dt>IATI XML file</dt>
        <dd><code>
          <a :href="`${baseURL}/iati/2.03/LR.xml`">{{baseURL}}/iati/2.03/LR.xml</a></code></dd>
      </dl>
      <p></p>
      <b-modal id="customise-fields" title="Customise columns" size="xl" scrollable ok-only>
        <b-row>
          <b-col md="8">
            <b-card-group columns>
              <b-card>
                <b-form-group label="Basic columns" label-class="font-weight-bold">
                  <b-form-checkbox-group
                    v-model="selectedHeaders[selectedTemplateOption]"
                    stacked
                    :options="headers.basic"
                  ></b-form-checkbox-group>
                </b-form-group>
              </b-card>
              <b-card>
                <b-form-group label="Disbursements" label-class="font-weight-bold">
                  <b-form-checkbox-group
                    v-model="selectedHeaders[selectedTemplateOption]"
                    stacked
                    :options="headers.disbursement"
                  ></b-form-checkbox-group>
                </b-form-group>
              </b-card>
              <b-card>
                <b-form-group label="MTEF Projections" label-class="font-weight-bold">
                  <b-form-checkbox-group
                    v-model="selectedHeaders[selectedTemplateOption]"
                    stacked
                    :options="headers.mtef"
                  ></b-form-checkbox-group>
                </b-form-group>
              </b-card>
              <b-card>
                <b-form-group label="Counterpart Funding" label-class="font-weight-bold">
                  <b-form-checkbox-group
                    v-model="selectedHeaders[selectedTemplateOption]"
                    stacked
                    :options="headers.counterpart_funding"
                  ></b-form-checkbox-group>
                </b-form-group>
              </b-card>
              <b-card v-if="headers.custom.length > 0">
                <b-form-group label="Custom headers" label-class="font-weight-bold">
                  <b-form-checkbox-group
                    v-model="selectedHeaders[selectedTemplateOption]"
                    stacked
                    :options="headers.custom"
                  ></b-form-checkbox-group>
                </b-form-group>
              </b-card>
            </b-card-group>
          </b-col>
          <b-col md="4">
            <b-card bg-variant="secondary" text-variant="white" header="Selected columns">
              <p>Select columns on the left. Drag below to reorder.</p>
              <draggable v-model="selectedHeaders[selectedTemplateOption]"
                ghost-class="hidden" @start="drag=true" @end="drag=false">
                 <div v-for="column in selectedHeaders[selectedTemplateOption]" :key="column"
                  class="draggable-item">
                  <b-badge variant="light">{{ column }}</b-badge>
                </div>
              </draggable>
            </b-card>
            <hr />
            <b-form-group label="Add a new custom column"
              description="This will create an additional (empty) column in your spreadsheet. You can use this for collecting data that might not be captured in the Dashboard.">
              <b-form-input placeholder="Enter new column name" v-model="newColumnName"
              size="sm"></b-form-input>
            </b-form-group>
            <b-form-group>
              <b-btn size="sm" @click.prevent="addColumn">Add column</b-btn>
            </b-form-group>
          </b-col>
        </b-row>
      </b-modal>
    </template>
  </div>
</template>
<script>
import { mapGetters } from 'vuex'
import DownloadFile from '~/components/DownloadFile.vue'
export default {
  components: {
    DownloadFile
  },
  head() {
    return {
      title: `Export data | ${this.$config.title}`
    }
  },
  data() {
    return {
      selectedTemplateOption: 'disbursements',
      templateOptions: [
        {
            'text': 'Disbursements (quarterly)',
            'value': 'disbursements',
            'help': 'AMCU quarterly disbursement template'
        },
        {
            'text': 'MTEF projections (annually)',
            'value': "mtef",
            'help': 'Annual MTEF forward projections template'
        },
        /*
        {
            'text': 'Detailed update (ad hoc)',
            'value': 'detail',
            'help': 'Ad hoc detailed update template',
            disabled: true
        },*/
      ],
      templateOptionsImport: [
        {
            'text': 'Disbursements (quarterly)',
            'value': 'disbursements',
            'help': 'AMCU quarterly disbursement template'
        },
        {
            'text': 'MTEF projections (annually)',
            'value': "mtef",
            'help': 'Annual MTEF forward projections template'
        },
        {
            'text': 'Automatically detect',
            'value': 'detect',
            'help': 'Automatically detect and import/update all fields',
            disabled: true
        }
      ],
      importTemplate: {
        template_type: "disbursements",
        file: null,
        isBusy: false
      },
      importPSIP: {
        fiscal_year: null,
        file: null,
        isBusy: false
      },
      quarters: [],
      selectedQuarter: null,
      fys: [],
      currentFY: null,
      currencies: [],
      selectedCurrency: "USD",
      reportingOrganisations: [],
      selectedReportingOrganisation: "all",
      file: null,
      headers: {
        basic: [],
        mtef: [],
        disbursement: [],
        custom: []
      },
      selectedHeaders: {},
      requiredFields: ['ID', 'Activity Status',
          'Activity Dates (Start Date)', 'Activity Dates (End Date)'],
      newColumnName: "",
      baseURL: this.$config.baseURL,
      isBusy: true,
      importMessagesTemplate: [],
      importMessagesPSIP: [],
      projectBriefDonorID: null
    }
  },
  computed: {
    selectedTemplateOptionImportDescription() {
      return this.templateOptionsImport.reduce(
      (obj, item, index) => {
        obj[item['value']] = item['help']
        return obj
          },
      {})[this.importTemplate.template_type]
    },
    projectBriefDonorName() {
      if (this.projectBriefDonorID == null) {
        return "(Select a donor)"
      }
      return this.reportingOrganisations.filter(org => {
        return org.id == this.projectBriefDonorID
      })[0].name
    },
    selectedTemplateOptionDescription() {
      return this.templateOptions.reduce(
      (obj, item, index) => {
        obj[item['value']] = item['help']
        return obj
          },
      {})[this.selectedTemplateOption]
    },
    quarter() {
      const monthsQuarters = {
        1: 3, 2: 3, 3: 3, 4: 4, 5: 4, 6: 4,
        7: 1, 8: 1, 9: 1, 10: 2, 11: 2, 12: 2
      }
      return monthsQuarters[(new Date).getMonth()]
    },
    selectedReportingOrganisationName() {
      if (this.selectedReportingOrganisation == 'all') {
        return "All Donors"
      }
      return this.reportingOrganisations.filter(org => {
        return org.id == this.selectedReportingOrganisation
      })[0].name
    },
    templateDownloadFilename() {
      return `AMCU ${this.selectedQuarter} Disbursements Template ${this.selectedReportingOrganisationName}.xlsx`
    },
    templateDownloadURL() {
      var params = {
          'reporting_organisation_id': this.selectedReportingOrganisation,
          'currency_code': this.selectedCurrency,
          'template': this.selectedTemplateOption,
          'headers': this.selectedHeaders[this.selectedTemplateOption]
      }
      var params_url = Object.entries(params).map(([key, val]) => `${key}=${encodeURIComponent(val)}`).join('&')
      return `exports/export_template.xlsx?${params_url}`
    },
    ...mapGetters(['isAuthenticated', 'loggedInUser'])
  },
  methods: {
    async submitFile(data, url, messages) {
      this.$set(this, messages, [])
      this.$set(data, 'isBusy', true)
      let postData = new FormData()
      Object.entries(data).forEach(d => {
        if (d[0] != 'file') {
          postData.set(d[0], d[1])
        }
      })
      postData.set('file', data.file, data.file.name)
      await this.$axios.post(url, postData)
        .then(response => {
          this.$root.$bvToast.toast(response.data.msg, {
            title: 'Data uploaded',
            autoHideDelay: 7000,
            variant: 'success',
            solid: true
          })
          this.$set(this, messages, [response.data.msg].concat(response.data.messages ? response.data.messages : []))
          data.file = null
        })
        .catch(error => {
          console.log('Error uploading file', error)
        })
      this.$set(data, 'isBusy', false)
    },
    addColumn: function() {
      this.selectedHeaders[this.selectedTemplateOption].push(this.newColumnName)
      this.headers.custom.push(this.newColumnName)
    },
    setupForm: function() {
      this.$axios
      .get(`filters/available_fys_fqs.json`)
      .then(response => {
        this.fys = response.data.fys
        this.currentFY = response.data.current_fy
        this.importPSIP.fiscal_year = response.data.current_fy
        this.quarters = response.data.fys_fqs
        this.selectedQuarter = response.data.previous_fy_fq
        this.selectedTemplateOption = response.data.mtef_or_disbursements
        this.importTemplate.template_type = response.data.mtef_or_disbursements
      });
      this.$axios
      .get(`spreadsheet_headers.json`)
      .then(response => {
        this.headers = {
          basic: this.checkRequired(response.data.headers),
          mtef: this.checkRequired(response.data.mtef_headers),
          disbursement: this.checkRequired(response.data.disbursement_headers),
          counterpart_funding: this.checkRequired(response.data.counterpart_funding_headers),
          custom: []
        }
        this.selectedHeaders = response.data.selected
      });
      this.$axios
      .get(`filters/currency.json`)
      .then(response => {
          this.currencies = response.data.currencies
      });
      this.$axios
      .get(`filters/reporting_organisation.json`)
      .then(response => {
          this.reportingOrganisations = response.data.reporting_organisations
      });
      this.isBusy = false
    },
    checkRequired: function(data) {
      return data.map((item) =>
        {
          return {
            'text': item,
            'value': item,
            disabled: this.requiredFields.includes(item)
          }
        }
      )
    }
  },
  mounted: function() {
    this.setupForm()
  }
}
</script>
