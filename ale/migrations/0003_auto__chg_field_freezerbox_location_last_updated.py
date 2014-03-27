# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'FreezerBox.location_last_updated'
        db.alter_column('ale_freezerbox', 'location_last_updated', self.gf('django.db.models.fields.DateField')(auto_now=True, null=True, auto_now_add=True))

    def backwards(self, orm):

        # Changing field 'FreezerBox.location_last_updated'
        db.alter_column('ale_freezerbox', 'location_last_updated', self.gf('django.db.models.fields.DateField')(auto_now=True, auto_now_add=True))

    models = {
        'ale.aleexperiment': {
            'Meta': {'object_name': 'AleExperiment'},
            'ale_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'instrument': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ale.Instrument']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'person': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'simulation': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'ale.aleid': {
            'Meta': {'unique_together': "(('ale_experiment', 'ale_id'),)", 'object_name': 'AleId'},
            'ale_experiment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ale.AleExperiment']"}),
            'ale_id': ('django.db.models.fields.IntegerField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'starting_strain': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['ale.Isolate']", 'null': 'True', 'blank': 'True'})
        },
        'ale.flask': {
            'Meta': {'unique_together': "(('ale_id', 'flask_number'),)", 'object_name': 'Flask'},
            'ale_id': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ale.AleId']"}),
            'comments': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'flask_number': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'media': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ale.Media']"})
        },
        'ale.freezerbox': {
            'Meta': {'object_name': 'FreezerBox'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'default': "'None'", 'max_length': '500'}),
            'location_last_updated': ('django.db.models.fields.DateField', [], {'default': "'2013-05-02'", 'auto_now': 'True', 'null': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'number': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'ale.instrument': {
            'Meta': {'object_name': 'Instrument'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'ale.isolate': {
            'Meta': {'unique_together': "(('flask', 'isolate_number'),)", 'object_name': 'Isolate'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'flask': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ale.Flask']"}),
            'freezer_box': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ale.FreezerBox']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_population': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'isolate_number': ('django.db.models.fields.IntegerField', [], {}),
            'parent_isolate': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ale.Isolate']", 'null': 'True', 'blank': 'True'}),
            'person': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'ale.media': {
            'Meta': {'object_name': 'Media'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'other': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'stirring_speed': ('django.db.models.fields.FloatField', [], {'default': '1123'}),
            'temperature': ('django.db.models.fields.FloatField', [], {'default': '37'}),
            'volume': ('django.db.models.fields.FloatField', [], {'default': '25'})
        }
    }

    complete_apps = ['ale']