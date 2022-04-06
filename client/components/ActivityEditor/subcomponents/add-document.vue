<template>
  <div>
    <b-modal id="add-document-modal" title="Add document"
      ok-title="Upload" @ok="submitFile" :ok-disabled="loading">
      <b-form-group label="Title"
        label-cols-sm="3"
        :state="newDocument.validation.title">
        <b-input
          v-model="newDocument.title"
          required
          :state="newDocument.validation.title">
        </b-input>
      </b-form-group>
      <b-form-group label="Type"
        label-cols-sm="3"
        :state="newDocument.validation.categoryCodes">
        <client-only>
          <v-select :options="categories" v-model="newDocument.categoryCodes" multiple
          label="text" :reduce="item => item.value" :get-option-label="getDocumentLabel">
          </v-select>
        </client-only>
      </b-form-group>
      <b-form-group
        label="Upload file"
        label-cols-sm="3"
        :state="newDocument.validation.file">
        <b-form-file
        v-model="newDocument.file"
        required
        :state="newDocument.validation.file"></b-form-file>
      </b-form-group>
      <p class="text-muted" v-if="fileSizeWarning">Warning: your file is very large and will take some time to upload.
        You may wish to consider reducing the file size, for example by scanning in at a lower resolution.</p>
    </b-modal>
  </div>
</template>
<script>
export default {
  name: 'AddDocument',
  middleware: 'auth',
  loading: false,
  props: ['activity', 'documents', 'api_routes', 'categories'],
  data() {
    return {
      newDocument: {
        validation: {
        }
      },
      loading: false,
      activityID: this.activity.id,
      warnFileSize: '10000000'
    }
  },
  methods: {
    getDocumentLabel(item) {
      return item.text
    },
    submitFile(bvEvent) {
      bvEvent.preventDefault()
      if (!this.newDocument.title || !this.newDocument.file) {
        if (!this.newDocument.title) { this.$set(this.newDocument.validation, 'title', false) }
        if (!this.newDocument.file) { this.$set(this.newDocument.validation, 'file', false) }
        this.$bvToast.toast("Please enter a title and select a file.", {
          title: 'Error',
          variant: 'danger'
        })
        return false
      } else {
        this.newDocument.validation = {}
      }
      const API_URL = this.api_routes.documents
      const postData = new FormData()
      postData.append('file', this.newDocument.file, this.newDocument.file.name)
      postData.append('activity_id', this.activityID)
      postData.append('title', this.newDocument.title)
      postData.append('categoryCodes', this.newDocument.categoryCodes)
      this.loading = true
      this.$axios.post(API_URL, postData)
        .then(response => {
          this.documents.push(response.data.document)
          this.$root.$bvToast.toast(`Your document was uploaded and attached to this activity.`, {
            title: 'Document uploaded',
            autoHideDelay: 3000,
            variant: 'success'
          })
          this.newDocument = { validation: {} }
          this.$bvModal.hide('add-document-modal')
          this.loading = false
        })
        .catch(error => {
          this.$root.$bvToast.toast(`Sorry, there was an unexpected error uploading your document.`, {
            title: 'Error',
            autoHideDelay: 3000,
            variant: 'danger'
          })
          this.loading = false
        })
      return
    }
  },
  computed: {
    fileSize() {
      if (this.newDocument.file) {
        var size_kb = this.newDocument.file.size / 1000
        return `${size_kb} KB`
      }
    },
    fileSizeWarning() {
      if (!this.newDocument.file) {
        return false
      } else if (this.newDocument.file.size > this.warnFileSize) {
        return true
      }
      return false
    }
  }
}
</script>