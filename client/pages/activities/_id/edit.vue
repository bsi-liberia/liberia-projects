<template>
  <div>
    <ActivityEditor />
  </div>
</template>
<style>
</style>
<script>
import Vue from 'vue'
  // ACTIVITIES APP

Vue.config.devtools = true

import ActivityEditor from '~/components/ActivityEditor.vue'

export default {
  components: {
    ActivityEditor,
  },
  data() {
    return {
    }
  }
}
</script>
