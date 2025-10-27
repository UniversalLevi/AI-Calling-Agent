/**
 * Initialize Voice Configuration Script
 * ====================================
 * 
 * This script initializes the voice and humanization settings
 * in the database to fix the 500 errors in the dashboard.
 */

const mongoose = require('mongoose');
const SystemConfig = require('../models/SystemConfig');

// Connect to MongoDB
const connectDB = async () => {
  try {
    const conn = await mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/sara-dashboard', {
      useNewUrlParser: true,
      useUnifiedTopology: true,
    });
    console.log(`MongoDB Connected: ${conn.connection.host}`);
  } catch (error) {
    console.error('Database connection error:', error);
    process.exit(1);
  }
};

// Initialize voice configurations
const initVoiceConfigs = async () => {
  try {
    console.log('🎤 Initializing voice configurations...');
    
    // Voice settings that the dashboard expects
    const voiceConfigs = [
      {
        name: 'tts_provider',
        category: 'voice',
        value: 'openai',
        dataType: 'string',
        description: 'TTS voice provider (openai, azure, google)',
        validation: {
          options: ['openai', 'azure', 'google']
        }
      },
      {
        name: 'tts_voice_english',
        category: 'voice',
        value: 'nova',
        dataType: 'string',
        description: 'English TTS voice',
        validation: {
          options: ['nova', 'shimmer', 'echo', 'fable', 'onyx', 'alloy']
        }
      },
      {
        name: 'tts_voice_hindi',
        category: 'voice',
        value: 'shimmer',
        dataType: 'string',
        description: 'Hindi TTS voice',
        validation: {
          options: ['shimmer', 'nova', 'alloy']
        }
      },
      {
        name: 'tts_speed',
        category: 'voice',
        value: 1.0,
        dataType: 'number',
        description: 'Speech speed multiplier',
        validation: {
          min: 0.5,
          max: 2.0
        }
      },
      {
        name: 'tts_language_preference',
        category: 'voice',
        value: 'auto',
        dataType: 'string',
        description: 'Language preference for TTS',
        validation: {
          options: ['auto', 'english', 'hindi', 'mixed']
        }
      },
      {
        name: 'humanized_mode',
        category: 'voice',
        value: false,
        dataType: 'boolean',
        description: 'Enable humanized speech mode'
      },
      {
        name: 'filler_frequency',
        category: 'voice',
        value: 0.15,
        dataType: 'number',
        description: 'Frequency of filler words',
        validation: {
          min: 0.0,
          max: 1.0
        }
      },
      {
        name: 'hindi_bias_threshold',
        category: 'voice',
        value: 0.8,
        dataType: 'number',
        description: 'Threshold for Hindi language bias',
        validation: {
          min: 0.0,
          max: 1.0
        }
      },
      {
        name: 'emotion_detection_mode',
        category: 'voice',
        value: 'hybrid',
        dataType: 'string',
        description: 'Emotion detection mode',
        validation: {
          options: ['hybrid', 'keyword', 'gpt']
        }
      },
      {
        name: 'enable_spoken_tone_converter',
        category: 'voice',
        value: true,
        dataType: 'boolean',
        description: 'Enable spoken tone converter'
      },
      {
        name: 'enable_micro_sentences',
        category: 'voice',
        value: true,
        dataType: 'boolean',
        description: 'Enable micro sentences'
      },
      {
        name: 'enable_semantic_pacing',
        category: 'voice',
        value: true,
        dataType: 'boolean',
        description: 'Enable semantic pacing'
      }
    ];

    let createdCount = 0;
    let updatedCount = 0;

    for (const config of voiceConfigs) {
      const existingConfig = await SystemConfig.findOne({ name: config.name });
      
      if (existingConfig) {
        // Update existing config
        existingConfig.value = config.value;
        existingConfig.dataType = config.dataType;
        existingConfig.description = config.description;
        existingConfig.validation = config.validation;
        await existingConfig.save();
        updatedCount++;
        console.log(`✅ Updated: ${config.name}`);
      } else {
        // Create new config
        await SystemConfig.create(config);
        createdCount++;
        console.log(`✅ Created: ${config.name}`);
      }
    }

    console.log(`\n🎉 Voice configuration initialization complete!`);
    console.log(`   Created: ${createdCount} configurations`);
    console.log(`   Updated: ${updatedCount} configurations`);
    
  } catch (error) {
    console.error('❌ Error initializing voice configurations:', error);
    throw error;
  }
};

// Main execution
const main = async () => {
  try {
    await connectDB();
    await initVoiceConfigs();
    console.log('\n✅ Voice configurations initialized successfully!');
    process.exit(0);
  } catch (error) {
    console.error('❌ Script failed:', error);
    process.exit(1);
  }
};

// Run the script
if (require.main === module) {
  main();
}

module.exports = { initVoiceConfigs };









