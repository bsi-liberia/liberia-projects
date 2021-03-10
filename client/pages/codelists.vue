<template>
  <div>
    <h1>Manage codelists</h1>
    <b-tabs content-class="mt-3">
      <b-tab title="Organisations" active>
        <h3>Organisations</h3>
        <b-table class="table codelists-data"
          data-codelist="organisation"
          id="table-organisation"
          :fields="organisationFields"
          :items="organisations"
          :busy="isBusy">
          <template v-slot:table-busy>
            <div class="text-center my-2">
              <b-spinner class="align-middle" label="Loading..."></b-spinner>
              <strong>Loading...</strong>
            </div>
          </template>
          <template v-slot:cell(name)="data">
            <div class="form-group">
              <label class="control-label sr-only">Name</label>
              <b-input
                name="name" :value="data.item.name"
                @change="updateCode($event, 'organisation', data, 'name')"
                :state="data.item.validation.name">
              </b-input>
            </div>
          </template>
          <template v-slot:cell(acronym)="data">
            <div class="form-group">
              <label class="control-label sr-only">Acronym</label>
              <b-input
                name="acronym" :value="data.item.acronym"
                @change="updateCode($event, 'organisation', data, 'acronym')"
                :state="data.item.validation.acronym">
              </b-input>
            </div>
          </template>
          <template v-slot:cell(type)="data">
            <div class="form-group">
              <label class="control-label sr-only">Type</label>
              <b-select id="_type" name="_type"
                :options="organisationTypeOptions"
                v-model="data.item._type"
                @change="updateCode($event, 'organisation', data, '_type')"
                :state="data.item.validation._type">
              </b-select>
            </div>
          </template>
          <template v-slot:cell(code)="data">
            <div class="form-group">
              <label class="control-label sr-only">IATI Code</label>
              <b-input
                name="code" :value="data.item.code"
                @change="updateCode($event, 'organisation', data, 'code')"
                :state="data.item.validation.code">
              </b-input>
            </div>
          </template>
          <template v-slot:cell(budget_code)="data">
            <div class="form-group">
              <label class="control-label sr-only">Budget Code</label>
              <b-input
                name="budget_code" :value="data.item.budget_code"
                @change="updateCode($event, 'organisation', data, 'budget_code')"
                :state="data.item.validation.budget_code">
              </b-input>
            </div>
          </template>
          <template v-slot:cell(delete)="data">
              <b-button variant="link" class="text-danger"
              size="sm" @click="deleteCode('organisation', data)">
              <font-awesome-icon :icon="['fa', 'trash-alt']" />
            </b-button>
          </template>
        </b-table>
        <b-btn variant="success" @click="addCode('organisation')">
          <font-awesome-icon :icon="['fa', 'plus']" />
          Add organisation
        </b-btn>
      </b-tab>
      <b-tab :title="codelist.name" v-for="codelist in codelist_names" v-bind:key="codelist.code">
        <h3>{{ codelist.name }}</h3>
        <b-table class="table codelists-data"
          :fields="['code', 'name', 'delete']"
          :items="codelist_codes[codelist.code]"
          :busy="isBusy">
          <template v-slot:table-busy>
            <div class="text-center my-2">
              <b-spinner class="align-middle" label="Loading..."></b-spinner>
              <strong>Loading...</strong>
            </div>
          </template>
          <template v-slot:cell(code)="data">
            <div class="form-group">
              <label class="control-label sr-only">Code</label>
              <b-input class="code"
                name="code" :value="data.item.code"
                @change="updateCode($event, codelist.code, data, 'code')"
                :state="data.item.validation.code">
              </b-input>
            </div>
          </template>
          <template v-slot:cell(name)="data">
            <div class="form-group">
              <label class="control-label sr-only">Name</label>
              <b-input
                name="name" :value="data.item.name"
                @change="updateCode($event, codelist.code, data, 'name')"
                :state="data.item.validation.name">
              </b-input>
            </div>
          </template>
          <template v-slot:cell(delete)="data">
            <b-button variant="link" class="text-danger"
              size="sm" @click="deleteCode(codelist.code, data)">
              <font-awesome-icon :icon="['fa', 'trash-alt']" />
            </b-button>
          </template>
        </b-table>
        <b-btn variant="success" @click="addCode(codelist.code)">
          <font-awesome-icon :icon="['fa', 'plus']" />
          Add code
        </b-btn>
      </b-tab>
    </b-tabs>
  </div>
</template>
<script>
  export default {
    data() {
      return {
        codelist_codes: {},
        codelist_names: [],
        organisations: [],
        organisationFields: [{
          key: 'name'
        },
        {
          key: 'acronym'
        },
        {
          key: 'type'
        },
        {
          key: 'code',
          label: 'IATI Organisation ID'
        },
        {
          key: 'budget_code',
          label: 'GoL Budget Code'
        },
        {
          key: 'delete'
        }],
        organisationTypeOptions: [{
          value: 'donor',
          text: 'Donor'
        },
        {
          value: 'gol',
          text: 'Govt of Liberia'
        },
        {
          value: 'ngo',
          text: 'NGO'
        }],
        isBusy: true
      }
    },
    head() {
      return {
        title: `Codelists | ${this.$config.title}`
      }
    },
    middleware: 'auth',
    mounted: function() {
      this.getCodelistsData()
    },
    methods: {
      async getCodelistsData() {
        await this.$axios.get(`codelists/`)
          .then(response => {
            this.codelist_codes = Object.entries(response.data.codelist_codes).reduce((codelists, item) => {
              codelists[item[0]] = item[1].reduce((codelist_items, codelist_item) => {
                if (codelist_item.name != '') {
                  codelist_item['validation'] = {}
                  codelist_items.push(codelist_item)
                }
                return codelist_items
              }, [])
              return codelists
            }, {})
            this.codelist_names = response.data.codelist_names
            this.organisations = response.data.organisations.map(organisation => {
              return {'validation': {},...organisation}
            })
          })
          this.isBusy = false
      },
      updateCode(newValue, codelist_code, code, attr) {
        var data = {
          'codelist_code': codelist_code,
          'id': code.item.id,
          'attr': attr,
          'value': newValue,
        }
        this.$axios.post("codelists/update/", data)
          .then(response => {
            this.$set(code.item.validation, attr, true)
          })
          .catch(error => {
            this.$set(code.item.validation, attr, false)
          })

      },
      addCode(codelist) {
        var data = {
          "codelist_code": codelist,
          "code": "CODE",
          "name": "NAME"
        }

        this.$axios.post("codelists/new/", data)
        .then(response => {
          if (response.data == 'ERROR'){
              alert("There was an error creating that code.");
          } else {
            var data = {
              "id": response.data,
              "codelist_code": codelist,
              "code": "CODE",
              "name": "NAME",
              "validation": {}
            }
            if (codelist == "organisation") {
              this.organisations.push(data)
            } else {
              this.codelist_codes[codelist].push(data)
            }
          }
        }
        )
      },
      deleteCode(codelist, code) {
        this.$bvModal.msgBoxConfirm('Are you sure you want to delete this code? This action cannot be undone!', {
          title: 'Confirm delete',
          okVariant: 'danger',
          okTitle: 'Confirm delete',
          hideHeaderClose: false,
          centered: true
        })
        .then(value => {
          if (value) {
            var data = {
              'codelist_code': codelist,
              'id': code.item.id,
              "action": "delete"
            }
            this.$axios.post("codelists/delete/", data)
             .then(response => {
                if (response.data == 'ERROR'){
                  alert("There was an error deleting that code.");
                } else {
                  if (codelist == 'organisation') {
                    this.$delete(this.organisations, code.index)
                  } else {
                    this.$delete(this.codelist_codes[codelist], code.index)
                  }
                }
              }
            )
          }
        })
        .catch(err => {
          alert("Sorry, there was an error, and that code couldn't be deleted.")
        })
      }
    }
  }
</script>
