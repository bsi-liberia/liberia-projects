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
              v-for="category in data.item.categories" v-bind:key="category">{{ category }}</span>
        </template>
        <template v-slot:cell(date)="data">
          {{ data.item.document_date || '' }}
        </template>
      </b-table>
    </div>
</template>
<script>
export default {
  data() {
    return {
      documents: []
    }
  },
  props: ["api_routes"],
  mounted: function() {
    this.setupDocuments()
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