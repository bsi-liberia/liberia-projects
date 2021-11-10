<template>
  <b-card title="Import data">
    <b-card-text>
      <p class="lead">Upload new data from Client Connection</p>
      <b-row>
        <b-col>
          <b-form-file
            v-model="uploadFiles"
            :file-name-formatter="formatNames"
            multiple>
          </b-form-file>
        </b-col>
      </b-row>
      <b-row class="mt-2">
        <b-col>
          <b-btn variant="primary" @click="submitFile">Upload</b-btn>
        </b-col>
      </b-row>
    </b-card-text>
  </b-card>
</template>
<script>
export default {
  data() {
    return {
      uploadFiles: []
    }
  },
  methods: {
    formatNames(files) {
      return files.length === 1 ? files[0].name : `${files.length} files selected`
    },
    async submitFile() {
      let postData = new FormData()
      for (let file of this.uploadFiles) {
        postData.append('file', file, file.name)
      }
      const url = '/client-connection/'
      await this.$axios.post(url, postData)
        .then(response => {
          this.$root.$bvToast.toast('Uploaded!', {
            title: 'Data uploaded',
            autoHideDelay: 7000,
            variant: 'success',
            solid: true
          })
          this.uploadFiles = []
          this.isBusy = true
          this.loadTransactions()
          this.isBusy = false
        })
        .catch(error => {
          console.log('Error uploading files', error)
        })
    },
    async loadTransactions() {
      const url = '/client-connection/transactions/'
      await this.$axios.get(url)
        .then(response => {
          this.transactions = response.data.transactions
          this.isBusy = false
        })
    }
  }
}
</script>
