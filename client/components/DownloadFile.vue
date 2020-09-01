<template>
  <div>
    <template v-if="preparingFile">
      <b-btn variant="secondary" :size="size" @click="getActivitiesFile">
        <b-spinner label="Preparing" small></b-spinner> Preparing file...
      </b-btn>
    </template>
    <template v-else>
      <b-btn :variant="variant" @click="getActivitiesFile" :size="size">
        <font-awesome-icon :icon="icon" /> {{ label }}
      </b-btn>
    </template>
  </div>
</template>
<script>
import { saveAs } from 'file-saver'
export default {
  data() {
    return {
      preparingFile: false
    }
  },
  props: {
    'label': String,
    'variant': String,
    'file-name': String,
    'url': String,
    'size': {
      type: String,
      default: null
    },
    'icon': {
      type: Array,
      default: function () {
        return ['fa', 'download']
      }
    }
  }
  ,
  methods: {
    async getActivitiesFile() {
      this.preparingFile = true
      await this.$axios({url: this.url,
        method: 'GET',
        responseType: 'blob'}).then(response => {
          console.log("response", response)
        if (response.status === 200) {
          saveAs(
            new Blob([response.data]),
            this.fileName
          )
        } else if (response.status === 500) {
          this.$bvToast.toast(`Sorry, something went wrong, and the file could not be downloaded.`, {
            title: "Error.",
            variant: "danger"
          })
        }
      })
      .catch(error => {
        this.$bvToast.toast(`Sorry, something went wrong, and the file could not be downloaded.`, {
          title: "Error.",
          variant: "danger"
        })
      })
      this.preparingFile = false
    }
  }
}
</script>