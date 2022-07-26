<template>
  <div>
    <h1>Sectors</h1>
    <hr />
    <AggregatesTop
      dimension="mtef-sector"
      dimension-label="Sector" />
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
      title: `Sectors | ${this.$config.title}`,
      meta: [
        { hid: 'twitter:title', name: 'twitter:title', content: `Sectors | ${this.$config.title}` },
        { hid: 'og:title', name: 'og:title', content: `Sectors | ${this.$config.title}` },
      ]
    }
  }
}
</script>
