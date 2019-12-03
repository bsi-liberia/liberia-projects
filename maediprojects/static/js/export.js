Vue.config.devtools = true
new Vue({
    el: "#app",
    delimiters: ["[[", "]]"],
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
            selectedTemplateOptionImport: "disbursements",
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
            quarters: [],
            selectedQuarter: null,
            fys: [],
            selectedFY: null,
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
            newColumnName: ""
        }
    },
    computed: {
        selectedTemplateOptionImportDescription() {
            return this.templateOptionsImport.reduce(
            (obj, item, index) => {
              obj[item['value']] = item['help']
              return obj
                },
            {})[this.selectedTemplateOptionImport]

        },
        selectedTemplateOptionDescription() {
            return this.templateOptions.reduce(
            (obj, item, index) => {
              obj[item['value']] = item['help']
              return obj
                },
            {})[this.selectedTemplateOption]
        },
        templateDownloadURL() {
            var params = {
                'reporting_organisation_id': this.selectedReportingOrganisation,
                'currency_code': this.selectedCurrency,
                'template': this.selectedTemplateOption,
                'headers': this.selectedHeaders[this.selectedTemplateOption]
            }
            var params_url = Object.entries(params).map(([key, val]) => `${key}=${encodeURIComponent(val)}`).join('&')
            return `${template_download_url}?${params_url}`
        }
    },
    methods: {
        addColumn: function() {
            this.selectedHeaders[this.selectedTemplateOption].push(this.newColumnName)
            this.headers.custom.push(this.newColumnName)
        },
        setupForm: function() {
            axios
            .get(`${api_base}filters/available_fys_fqs.json`)
            .then(response => {
                this.fys = response.data.fys
                this.selectedFY = response.data.current_fy
                this.quarters = response.data.fys_fqs
                this.selectedQuarter = response.data.previous_fy_fq
                this.selectedTemplateOption = response.data.mtef_or_disbursements
                this.selectedTemplateOptionImport = response.data.mtef_or_disbursements
            });
            axios
            .get(`${api_base}spreadsheet_headers.json`)
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
            axios
            .get(`${api_base}filters/currency.json`)
            .then(response => {
                this.currencies = response.data.currencies
            });
            axios
            .get(`${api_base}filters/reporting_organisation.json`)
            .then(response => {
                this.reportingOrganisations = response.data.reporting_organisations
            });
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
      if (window.location.hash && window.location.hash.split("#").length>0) {
        VueScrollTo.scrollTo(document.getElementById(window.location.hash.split("#")[1]), 500, {offset:-60})
      }
      this.setupForm()
    },
})