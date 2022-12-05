<template>
  <div>
    <b-table responsive fixed
      :fields="['title', 'type', 'date']"
      :items="documents">
      <template v-slot:cell(title)="data">
        <a :href="data.item.url">{{ data.item.title }}</a>
      </template>
      <template v-slot:cell(type)="data">
        <span class="badge badge-secondary"
            v-for="category in data.item.categories" v-bind:key="category">{{ categoriesObj[category] }}</span>
      </template>
      <template v-slot:cell(date)="data">
        {{ data.item.document_date || '' }}
      </template>
    </b-table>
    <b-btn variant="success" v-b-modal.add-document-modal>Add document</b-btn>
    <AddDocumentModal :documents="documents" :activity="activity"
      :categories="categories" :api_routes="api_routes" />
  </div>
</template>
<script>

import AddDocumentModal from '~/components/ActivityEditor/subcomponents/add-document.vue'
export default {
  data() {
    return {
      documents: []
    }
  },
  components: {
    AddDocumentModal
  },
  props: ["api_routes", "activity", "api_routes", "codelists"],
  mounted: function() {
    this.setupDocuments()
  },
  computed: {
    categories() {
      if (this.codelists.DocumentCategory == undefined) {
        return []
      }
      return this.codelists.DocumentCategory.filter(item => {
        return item.code.substr(0, 1) == 'A'
      }).map(item => {
        return { code: item.code, text: item.name, value: item.id}
      })
    },
    categoriesObj() {
      return this.categories.reduce((summary, item) => {
        summary[item.code] = item.text
        return summary
      }, {})
    }
  },
  methods: {
    async setupDocuments() {
      this.$axios
        .get(this.api_routes.documents)
        .then((response) => {
          this.documents = response.data.documents
        })
    }
  }
}
</script>