<template>
  <div>
    <UserEditor />
  </div>
</template>
<style>
</style>
<script>
import UserEditor from '~/components/UserEditor.vue'

export default {
  components: {
    UserEditor,
  },
  middleware: 'auth',
  data() {
    return {
    }
  }
}
</script>
