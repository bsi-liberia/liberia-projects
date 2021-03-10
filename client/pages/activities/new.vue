<template>
  <div>
    <ActivityEditor />
  </div>
</template>
<style>
</style>
<script>
import ActivityEditor from '~/components/ActivityEditor.vue'
export default {
  components: {
    ActivityEditor,
  },
  middleware: 'auth',
  data() {
    return {
    }
  }
}
</script>
