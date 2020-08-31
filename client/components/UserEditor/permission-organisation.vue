<template>
  <b-form-group :state="validation">
    <b-select
    :id="permission_id"
    :name="permission_id"
    class="form-control" :options="organisations"
    text-field="name" value-field="id" v-model="organisation_id"
    :state="validation">
    </b-select>
  </b-form-group>
</template>
<script>
export default {
  data() {
    return { validation: null }
  },
  props: ["permission_id", "organisation_id", "organisations", "updateChangedPermission"],
  watch: {
    organisation_id: {
      handler: function(newValue) {
        this.updateChangedPermission(this, this.permission_id, 'organisation_id', newValue)
        this.$emit('update:organisation_id', newValue)
      }
    }
  }
}
</script>