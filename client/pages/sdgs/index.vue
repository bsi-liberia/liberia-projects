<template>
  <div>
    <h1>Sustainable Development Goals</h1>
    <hr />
    <AggregatesTop
      dimension="sdg-goals"
      dimension-label="SDG" />
  </div>
</template>
<script>
import AggregatesTop from '~/components/AggregatesTop.vue'
export default {
  components: {
    AggregatesTop
  },
  head() {
    return {
      title: `Sustainable Development Goals | ${this.$config.title}`,
      meta: [
        { hid: 'twitter:title', name: 'twitter:title', content: `Sustainable Development Goals | ${this.$config.title}` },
        { hid: 'og:title', name: 'og:title', content: `Sustainable Development Goals | ${this.$config.title}` },
      ]
    }
  }
}
</script>
