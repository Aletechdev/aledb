# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Instrument'
        db.create_table('ale_instrument', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('ale', ['Instrument'])

        # Adding model 'AleExperiment'
        db.create_table('ale_aleexperiment', (
            ('ale_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('person', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('instrument', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ale.Instrument'])),
            ('simulation', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('ale', ['AleExperiment'])

        # Adding model 'Media'
        db.create_table('ale_media', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('temperature', self.gf('django.db.models.fields.FloatField')(default=37)),
            ('volume', self.gf('django.db.models.fields.FloatField')(default=25)),
            ('stirring_speed', self.gf('django.db.models.fields.FloatField')(default=1123)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('other', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('ale', ['Media'])

        # Adding model 'AleId'
        db.create_table('ale_aleid', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ale_id', self.gf('django.db.models.fields.IntegerField')()),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True)),
            ('ale_experiment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ale.AleExperiment'])),
            ('starting_strain', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['ale.Isolate'], null=True, blank=True)),
        ))
        db.send_create_signal('ale', ['AleId'])

        # Adding unique constraint on 'AleId', fields ['ale_experiment', 'ale_id']
        db.create_unique('ale_aleid', ['ale_experiment_id', 'ale_id'])

        # Adding model 'FreezerBox'
        db.create_table('ale_freezerbox', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('number', self.gf('django.db.models.fields.IntegerField')(default=1)),
        ))
        db.send_create_signal('ale', ['FreezerBox'])

        # Adding model 'Flask'
        db.create_table('ale_flask', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ale_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ale.AleId'])),
            ('flask_number', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('media', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ale.Media'])),
            ('comments', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal('ale', ['Flask'])

        # Adding unique constraint on 'Flask', fields ['ale_id', 'flask_number']
        db.create_unique('ale_flask', ['ale_id_id', 'flask_number'])

        # Adding model 'Isolate'
        db.create_table('ale_isolate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('isolate_number', self.gf('django.db.models.fields.IntegerField')()),
            ('parent_isolate', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ale.Isolate'], null=True, blank=True)),
            ('flask', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ale.Flask'])),
            ('is_population', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('freezer_box', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ale.FreezerBox'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=300, null=True, blank=True)),
            ('person', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal('ale', ['Isolate'])

        # Adding unique constraint on 'Isolate', fields ['flask', 'isolate_number']
        db.create_unique('ale_isolate', ['flask_id', 'isolate_number'])


    def backwards(self, orm):
        # Removing unique constraint on 'Isolate', fields ['flask', 'isolate_number']
        db.delete_unique('ale_isolate', ['flask_id', 'isolate_number'])

        # Removing unique constraint on 'Flask', fields ['ale_id', 'flask_number']
        db.delete_unique('ale_flask', ['ale_id_id', 'flask_number'])

        # Removing unique constraint on 'AleId', fields ['ale_experiment', 'ale_id']
        db.delete_unique('ale_aleid', ['ale_experiment_id', 'ale_id'])

        # Deleting model 'Instrument'
        db.delete_table('ale_instrument')

        # Deleting model 'AleExperiment'
        db.delete_table('ale_aleexperiment')

        # Deleting model 'Media'
        db.delete_table('ale_media')

        # Deleting model 'AleId'
        db.delete_table('ale_aleid')

        # Deleting model 'FreezerBox'
        db.delete_table('ale_freezerbox')

        # Deleting model 'Flask'
        db.delete_table('ale_flask')

        # Deleting model 'Isolate'
        db.delete_table('ale_isolate')


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